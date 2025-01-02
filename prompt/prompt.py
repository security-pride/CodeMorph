import os

def generate_prompt(method , sample, lang = ""):

    prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'code_perturbation')
    if lang:
        prompt_path = prompt_path + f"_{lang}"
        # print("prompt_path: ", prompt_path)
    prompt_file = os.path.join(prompt_path, method + '.txt')
    with open(prompt_file, 'r') as f:
        method_prompt = f.read()
    
    prompt = "There is a content composed of code and entry_point. The entry_point is the function signature of the code snippet to be rephrased.\n" + "There may be one or more functions, in the given funtion specified by the entry_point, " + method_prompt + "\n" + "If there is just one function, just do the rephrase with the given function. " + "The code is: " + sample["code"] + "\n" + "The entry_point: " + sample["entry_point"] + '\n'
    
    prompt = prompt + '\n' + f"Please output the all code including modified and unmodified parts and the entry_point only, without any other content.The format of the return should be like json format containing 'code' and 'entry_point'."

    return prompt

def generate_vote_prompt(code1, code2, lang):
    prompt = f"There are two code snippets in {lang} language. You need to compare the two code snippets to see if their semantics are consistent with ignoring the function signature.\n" + "The first code snippet is: " + code1 + "\n\n" + "The second code snippet is: " + code2 + "\n\n\n" + "Please just return True or False."

    return prompt