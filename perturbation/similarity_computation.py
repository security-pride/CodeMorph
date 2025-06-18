from .utils import lang_dict
import tempfile
import os
import subprocess
import zipfile
import json
from thefuzz import fuzz
import shutil
import re
lang_to_jplag = {
    "python": "python3",
    "cpp": "cpp",
    "c": "c",
    "java": "java",
    "go": "go",
    "rust": "rust",
}

def write_code(code, code_file):
    try:
        with open(code_file, 'w') as f:
            f.write(code)
    except Exception as e:
        print("Error writing f{code_file}:", e)
        return False
    return True

def get_result_file_zip(stdout):
    match = re.search(r'Successfully written the result:\s*([^\s]+\.zip)', stdout)

    if match:
        filename = match.group(1)  
        print("Extracted filename:", filename)
    else:
        print("No filename found.")

def jplag(original_code, rephrase_code, lang):

    current_working_directory = os.getcwd()

    current_file_directory = os.path.dirname(os.path.abspath(__file__))

    result_file = "temp"
    jar_file = os.path.join(current_file_directory, "../JPlag/cli/target/jplag-5.1.0-jar-with-dependencies.jar")
    
    with tempfile.TemporaryDirectory(delete=False) as code_dir:
        pass

    code_file1 = os.path.join(code_dir, f"original_code.{lang_dict[lang]}")
    code_file2 = os.path.join(code_dir, f"rephrase_code.{lang_dict[lang]}")

    if not write_code(original_code, code_file1):
        print("Error writing original code", original_code)
        return -1, -1
    if not write_code(rephrase_code, code_file2):
        print("Error writing rephrase code", rephrase_code)
        return -1, -1

    try:
        res = subprocess.run([  "java", 
                                "-jar", jar_file, code_dir, 
                                "-l", f"{lang_to_jplag[lang]}", 
                                "-r", result_file], 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                timeout=10
                            )

        shutil.rmtree(code_dir)

        max_score = 0
        avg_score = 0
        if res.returncode == 0:
            result_path = os.path.join(current_working_directory,f"{result_file}.zip")

            with zipfile.ZipFile(result_path, 'r') as zip_ref:
                file_name = "overview.json"
                if file_name in zip_ref.namelist():
                    with zip_ref.open(file_name) as f:
                        content = json.load(f)

                        max_score = content["top_comparisons"][0]["similarities"]["MAX"]
                        avg_score = content["top_comparisons"][0]["similarities"]["AVG"]

            os.remove(result_path)
        
            return round(max_score,2), round(avg_score,2)
    

        print("Error occurred while running the Java JAR:")
        print("Return code:", res.returncode)
        print("Error running JPlag: ", res.stderr)
        return -1, -1
    except subprocess.TimeoutExpired:
        print("Error: The command timed out.")
    except Exception as e:
        print("Error: An unexpected error occurred:", str(e))
    
    return -1, -1

def surface_similarity(original_code, rephrase_code, threshold: int = 50, stride_percent: float = 0.05):

    """
    MIT License

    Copyright (c) 2024 Yale-NLP

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    
    """

    # compute the scores
    scores = []

    longer_code = rephrase_code
    shorter_code = original_code

    if len(rephrase_code) < len(original_code):
        longer_code = original_code
        shorter_code = rephrase_code

    stride = max(int(len(shorter_code) * stride_percent), 1)
    max_score = -1
    if len(longer_code) == len(shorter_code):
        score = fuzz.ratio(longer_code, shorter_code)
        scores.append(score)
        # print(score)
        max_score = score
    else:
        for i in range(0, len(longer_code) - len(shorter_code), stride):
            score = fuzz.ratio(longer_code[i:i+len(shorter_code)], shorter_code)
            scores.append(score)
            # print(score)
            if score > max_score:
                max_score = score

    return max_score / 100
    
    
def compose_similarity_score(original_code, rephrase_code, lang):

    mu = 0.5
    nu = 0.5

    for i in range(2):
        max_score, avg_score = jplag(original_code, rephrase_code, lang)
        if max_score == -1:
            continue

        surface_score = surface_similarity(original_code, rephrase_code)

        if surface_score < 0:
            continue

        return round(max_score * nu + surface_score * mu, 4)
    
    return -1
    