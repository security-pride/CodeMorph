import subprocess
import tempfile
import os
import re

def detect_java_name(java_code):
    public_class_match = re.search(r'public\s+class\s+(\w+)', java_code)
    all_class_matches = re.findall(r'class\s+(\w+)', java_code)

    if public_class_match:
        return f"{public_class_match.group(1)}.java"
    
    if len(all_class_matches) == 1:
        return f"{all_class_matches[0]}.java"

    if len(all_class_matches) > 1:
        return f"{all_class_matches[0]}.java"
    
    return "Default.java"

def compile_cpp(code_file, output_path):
    return subprocess.run(["g++", code_file, "-o", output_path], capture_output=True, text=True, timeout=5)

def comile_java(code_file, temp_dir):
    return subprocess.run(["javac", code_file, "-d", temp_dir], capture_output=True, text=True,timeout=5)

def compile_go(code_file, output_path):
    return subprocess.run(["go", "build", "-o", output_path, code_file], capture_output=True, text=True, timeout=5)

def compile_rust(code_file, output_path):
    return subprocess.run(["rustc", code_file, "-o", output_path], capture_output=True, text=True, timeout=5)

def check_python_syntax(code_file):
    return subprocess.run(["pylint", code_file, "--errors-only"], capture_output=True, text=True, timeout=10)


def execute_compiler(code_file, lang):
    with tempfile.TemporaryDirectory() as temp_dir:
        if lang == "cpp" or lang == "c":
            output_path = os.path.join(temp_dir, 'main')
            return compile_cpp(code_file, output_path), output_path
        elif lang == "java":

            with open(code_file, 'r') as f:
                java_code = f.read()
            
            java_file_name = detect_java_name(java_code)
            java_file = os.path.join(temp_dir, java_file_name)
            with open(java_file, 'w') as f:
                f.write(java_code)

            return comile_java(java_file, temp_dir), temp_dir
        elif lang == "go":
            output_path = os.path.join(temp_dir, 'main')
            return compile_go(code_file, output_path), output_path
        elif lang == "rust":
            output_path = os.path.join(temp_dir, 'main')
            return compile_rust(code_file, output_path), output_path
        elif lang == "python":
            return check_python_syntax(code_file), temp_dir
        else:
            error_message = f"Unsupported language: {lang}"
            return subprocess.CompletedProcess(
                args=["compiler", code_file],  
                returncode=1,                  
                stdout="",                     
                stderr=error_message 
            )

def compile_code(code_file, lang):
    try:
        result, output_path = execute_compiler(code_file, lang)
        if result.returncode == 0:
            print(f"{code_file} compiled successfully, output file: {output_path}")
            return {"success": True, "message": result.stdout}
        else:
            print(f"{code_file} compiled failed: {result.stderr}")
            return {"success": False, "message": result.stderr}
    except Exception as e:
        print(f"Error when compile {code_file}: {e}")
        return {"success": False, "message": str(e)}

