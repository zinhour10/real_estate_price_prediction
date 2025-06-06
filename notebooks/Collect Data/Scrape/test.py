from llama_cpp import Llama

llm = Llama(
    model_path="./models/mistral/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=4,  # Adjust based on your CPU
    verbose=False
)

prompt = """Extract the land size in square meters (sqm) from this text. 
If dimensions like '20m x 30m' are mentioned, multiply them. 
If area like '98,514 sqm' is mentioned, extract that.
If no info, respond only: N/A

Text:
Now available for sale, 98,514 Sqm of land in Kompong Cham province.
Answer:"""

response = llm(prompt=prompt, max_tokens=32, stop=["\n"])
print(response["choices"][0]["text"].strip())
