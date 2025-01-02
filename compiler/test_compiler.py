from compiler import compile_code
import os

file_name = {
    "cpp": "hello_world.cpp",
    "java": "HelloWorl.java",
    "go": "hello_world.go",
    "rust": "hello_world.rs",
    "python": "hello_world.py",
    "c": "hello_world.c"
}



def test_compile_code():
    for lang, file in file_name.items():
        result = compile_code(os.path.join("test", file), lang)
        assert result["success"] == True
        print(f"{lang} test passed")

if __name__ == '__main__':
    test_compile_code()