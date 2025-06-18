import os
import json
import copy
import random
from datetime import datetime
import time
import numpy as np

from .utils import lang_dict, call_perturbation_llm, call_voter_llm
from ..compiler.compiler import compile_code
from .similarity_computation import compose_similarity_score, jplag, surface_similarity
from .method import transformation_classification, need_exec_method
from ..prompt.prompt import generate_prompt, generate_vote_prompt

# Modify it to your own model and corresponding API and URL
LLM_LIST = {
    'perturbation_llm': ['model', 'api_key', 'base_url'],
    'voter_llm_1': ['model', 'api_key', 'base_url'],
    'voter_llm_2': ['model', 'api_key', 'base_url'],
    'voter_llm_3': ['model', 'api_key', 'base_url'],
}





def rephrase_code(method, sample, lang):
    prompt = generate_prompt(method, sample, lang)

    rephrased_code = call_perturbation_llm(LLM_LIST['perturbation_llm'][0], LLM_LIST['perturbation_llm'][1], LLM_LIST['perturbation_llm'][2], prompt, lang)
    return rephrased_code

### only with one code
def get_code(code_file):
    # path = os.path.join('./test/method_test_file', method + '.cpp')
    with open(code_file, 'r') as f:
        data = json.load(f)
    return data

def rephrase_with_single_methods(method, lang, sample):
    try:
        res = rephrase_code(method, sample, lang)
    except Exception as e:
        print("error: ", e)
        return {
            "code": sample['code'],
            "entry_point": sample['entry_point']
        }, False

    res = res.replace('```json\n',"").replace('\n```', "").strip()

    try:
        res_json = json.loads(res)
    except Exception as e:
        print("error: ", e)
        return {
            "code": sample['code'],
            "entry_point": sample['entry_point']
        }, False

    code = res_json['code']
    print("entry_point: ", res_json['entry_point'])
    
    return {
        "code": code,
        "entry_point": res_json['entry_point']
    }, True

def vote_code(code1, code2, lang):
    prompt = generate_vote_prompt(code1, code2, lang)

    for i in range(3):
        try:
            result1 = call_voter_llm(LLM_LIST['voter_llm_1'][0], LLM_LIST['voter_llm_1'][1], LLM_LIST['voter_llm_1'][2], prompt, lang)
            result2 = call_voter_llm(LLM_LIST['voter_llm_2'][0], LLM_LIST['voter_llm_2'][1], LLM_LIST['voter_llm_2'][2], prompt, lang)
            result3 = call_voter_llm(LLM_LIST['voter_llm_3'][0], LLM_LIST['voter_llm_3'][1], LLM_LIST['voter_llm_3'][2], prompt, lang)

            true_time = 0

            if result1 == "True":
                true_time += 1
            if result2 == "True":
                true_time += 1
            if result3 == "True":
                true_time += 1
            
            if true_time >= 2:
                return True
            
        except Exception as e:
            print("error: ", e)
            continue
    
    return False

def get_timestamp():
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    return formatted_time

def rephrase_code_once(method, lang, sample, compiler_path, successfule_path, failed_path):
    
    task_id = sample['task_id']
    ## try two times
    for i in range(2):
        rephrased_code, succ = rephrase_with_single_methods(method, lang, sample)
        if not succ:
            continue

        output_file = os.path.join(compiler_path, f"{task_id}_{method}_{i}_{get_timestamp()}.{lang_dict[lang]}")
        with open(output_file, "w") as f:
            f.write(rephrased_code['code'])

        compile_res = compile_code(output_file, lang)
        if not compile_res['success']:
            print("Error in compiling the rephrased code with method: ", method, "sample: ", task_id, "error: ", compile_res['message'])
            continue

        vote_res = vote_code(sample["code"], rephrased_code["code"], lang)
        if vote_res:
            output_file = os.path.join(successfule_path, f"{task_id}_{method}_{get_timestamp()}.{lang_dict[lang]}")

            sample['code'] = rephrased_code['code']
            sample['entry_point'] = rephrased_code['entry_point']
            
            with open(output_file, "w") as f:
                f.write(rephrased_code['code'])
            
            return sample

        else:
            print(f"Vote failed with method: {method}, sample: {task_id}")
            output_file = os.path.join(failed_path, f"{task_id}_{method}_{i}_{get_timestamp()}.{lang_dict[lang]}")
            with open(output_file, "w") as f:
                f.write(rephrased_code['code'])
    return None


def boltzmann_selection(og_values, temperature):
    scaled_og = np.array(og_values) / temperature
    probabilities = np.exp(scaled_og) / np.sum(np.exp(scaled_og))
    chosen_index = np.random.choice(len(og_values), p=probabilities)
    return chosen_index

def create_intermediate_files(code_file):
    code_file_name_with_extension = os.path.basename(code_file)
    code_file_name = os.path.splitext(code_file_name_with_extension)[0]

    current_file_directory = os.path.dirname(os.path.abspath(__file__))

    compiler_path = os.path.join(current_file_directory,f"intermediate_files/{code_file_name}/compiler")
    os.makedirs(compiler_path, exist_ok=True)
    successfule_path = os.path.join(current_file_directory,f"intermediate_files/{code_file_name}/successful")
    os.makedirs(successfule_path, exist_ok=True)
    failed_path = os.path.join(current_file_directory,f"intermediate_files/{code_file_name}/failed")
    os.makedirs(failed_path, exist_ok=True)
    rephrase_path = os.path.join(current_file_directory,f"{code_file_name}/rephrased.jsonl")
    os.makedirs(os.path.dirname(rephrase_path), exist_ok=True)

    return compiler_path, successfule_path, failed_path, rephrase_path
    

def perturbation(lang, code_file, max_iter, similarity_threshold, temperature):
    method_score_after_trans = "method_score.json"
    compiler_path, successfule_path, failed_path, rephrase_path = create_intermediate_files(code_file)

    with open(code_file, 'r') as f:

        for line in f:
            
            sample = json.loads(line)
            start_time = time.time()
            iter_count = 0
            mini_similarity_score = 1

            original_code = sample['code']
            methods_classification_dict = copy.deepcopy(transformation_classification)
            methods_classification_list = [key for key in transformation_classification.keys()]

            ## we rename the code first
            for method in need_exec_method:
                sample_fork = copy.deepcopy(sample)
                rephrase_sample = rephrase_code_once(method = method, lang = lang, sample = sample_fork,
                                                    compiler_path=compiler_path,
                                                    successfule_path=successfule_path,
                                                    failed_path=failed_path
                                                )
                if rephrase_sample:
                    similarity_score = compose_similarity_score(original_code, rephrase_sample['code'], lang)
                    if similarity_score == -1:
                        print(f"Error in calculating the score, method: {method}, sample: {rephrase_sample['task_id']}, code: {rephrase_sample['code']}")
                        similarity_score = 1
                    else:
                        # mini_similarity_score = similarity_score
                        sample['code'] = rephrase_sample['code']
                        sample['entry_point'] = rephrase_sample['entry_point']

                        print(f"similarity_score: {similarity_score}, mini_similarity_score: {mini_similarity_score}, method: {method}, sample: {rephrase_sample['task_id']}")

                        mini_similarity_score = similarity_score
                        
                        with open(method_score_after_trans, 'a') as f:
                            f.write(json.dumps({
                                "method": method,
                                "similarity_score": similarity_score,
                                'mini_similarity_score': mini_similarity_score,
                                "sample": rephrase_sample['task_id'],
                                "error": similarity_score == -1
                            }) + ',\n')


            og  = 0
            optimization_gain_list = []
            

            ### first, initialize the method scores
            for method_list in methods_classification_list:
                
                iter_count += 1
                method = random.choice(methods_classification_dict[method_list])

                sample_fork = copy.deepcopy(sample)
                rephrase_sample = rephrase_code_once(method, lang, sample_fork,
                                                    compiler_path,
                                                    successfule_path,
                                                    failed_path
                                                )
        
                if rephrase_sample:
                    similarity_score = compose_similarity_score(original_code, rephrase_sample['code'], lang)

                    ### print result    
                    print(f"similarity_score: {similarity_score}, mini_similarity_score: {mini_similarity_score}, method: {method}, sample: {rephrase_sample['task_id']}")

                    with open(method_score_after_trans, 'a') as f:
                            f.write(json.dumps({
                                "method": method,
                                "similarity_score": similarity_score,
                                'mini_similarity_score': mini_similarity_score,
                                "sample": rephrase_sample['task_id'],
                                "error": similarity_score == -1,
                                'iter': iter_count
                            }) + ',\n')


                    og = 0
                    if similarity_score == -1:
                        similarity_score = 1
                        rephrase_sample = {}

                    elif similarity_score < mini_similarity_score:
                        
                        sample['code'] = rephrase_sample['code']
                        sample['entry_point'] = rephrase_sample['entry_point']
                        
                        og = mini_similarity_score - similarity_score
                        mini_similarity_score = similarity_score
                    
                    optimization_gain_list.append(og)

                else:
                    optimization_gain_list.append(0)
                    print(f"Error in rephrasing the code with method: {method}, sample: {sample['task_id']}")
                    with open(method_score_after_trans, 'a') as f:
                        f.write(json.dumps({
                            'sample': sample['task_id'],
                            "method": method,
                            "similarity_score": 1,
                            'mini_similarity_score': mini_similarity_score,
                            "error": "yes"
                        }) + ',\n')
                
            if len(optimization_gain_list) != len(methods_classification_list):
                print("Error in calculating the optimization_gain_list")
                print("optimization_gain_list: ", optimization_gain_list)
                print("methods_classification_list: ", methods_classification_list)
                exit()
                
            # temperature = 2
            while True:
                if iter_count >= max_iter:
                    break
                if mini_similarity_score <= similarity_threshold:
                    break

                iter_count += 1
                choose_index = boltzmann_selection(optimization_gain_list, temperature)

                choose_method_list = methods_classification_list[choose_index]
                choose_method = random.choice(methods_classification_dict[choose_method_list])

                sample_fork = copy.deepcopy(sample)
                rephrase_sample = rephrase_code_once(choose_method, lang, sample_fork,
                                                    compiler_path,
                                                    successfule_path,
                                                    failed_path
                                                )
                
                og = 0
                if rephrase_sample:
                    similarity_score = compose_similarity_score(original_code, rephrase_sample['code'], lang)

                    print(f"similarity_score: {similarity_score}, mini_similarity_score: {mini_similarity_score}, method: {choose_method}, sample: {rephrase_sample['task_id']}")

                    with open(method_score_after_trans, 'a') as f:
                        f.write(json.dumps({
                            "method": choose_method,
                            "similarity_score": similarity_score,
                            'mini_similarity_score': mini_similarity_score,
                            "sample": rephrase_sample['task_id'],
                            "error": similarity_score == -1,
                            'iter': iter_count
                        }) + ',\n')

                    if similarity_score == -1:
                        similarity_score = 1
                        rephrase_sample = {}
                    elif similarity_score <= mini_similarity_score:
                        sample['code'] = rephrase_sample['code']
                        sample['entry_point'] = rephrase_sample['entry_point']
                        og = mini_similarity_score - similarity_score
                        mini_similarity_score = similarity_score

                    optimization_gain_list[choose_index] = og
                
                else:
                    optimization_gain_list[choose_index] = 0

                    print(f"Error in rephrasing the code with method: {choose_method}, sample: {sample['task_id']}")
                    with open(method_score_after_trans, 'a') as f:
                        f.write(json.dumps({
                            'sample': sample['task_id'],
                            "method": choose_method,
                            "similarity_score": 1,
                            'mini_similarity_score': mini_similarity_score,
                            "error": "yes"
                        }) + ',\n')
                    


            print(f"sample {sample['task_id']} has been rephrased.")
            print(f"iter_count: {iter_count}, mini_similarity_score: {mini_similarity_score}")

        
            jplag_max_score, jplag_avg_score = jplag(original_code , sample['code'], lang)
            surface_score = surface_similarity(original_code, sample['code'])

            sample['score'] = {
                "jplag_max_score": jplag_max_score,
                "jplag_avg_score": jplag_avg_score,
                "surface_score": surface_score,
                "similarity_score": mini_similarity_score
            }
            sample['original_code'] = original_code

            with open(rephrase_path, 'a') as f:
                f.write(json.dumps(sample) + "\n")

            end_time = time.time()
            execution_time = end_time - start_time

            print(f"Execution time: {execution_time:.6f} seconds") 
    
            
                        
        