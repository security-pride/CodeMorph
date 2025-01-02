from openai import OpenAI


lang_dict = {
    "python": "py",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "go": "go",
    "rust": "rs",
}

def call_perturbation_llm(model_name, api_key,base_url,  prompt, lang, role_prompt=""):
    client = OpenAI(api_key = api_key, base_url = base_url)
    if role_prompt == "":
        role_prompt = f"You are a very useful {lang} code rephrasing assistant."
    
    response = client.chat.completions.create(
        model = model_name,
        messages = [
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": prompt + f"The returned code should be in {lang} language."}
        ],
        stream = False
    )

    return response.choices[0].message.content.strip()

def call_voter_llm(model_name, api_key, base_url, prompt, lang, role_prompt=""):
    client = OpenAI(api_key = api_key, base_url = base_url)
    if role_prompt == "":
        role_prompt = f"You are a very useful {lang} code comparison assistant, and you need to compare two pieces of code to see if their semantics are consistent."
    response = client.chat.completions.create(
        model = model_name,
        messages = [
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": prompt }
        ],
        stream = False
    )
    return response.choices[0].message.content.strip()



