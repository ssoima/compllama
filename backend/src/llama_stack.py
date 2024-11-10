from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url=f"http://localhost:5050")

response = client.inference.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a two-sentence poem about llama."}
    ],
    model="Llama3.2-90B-Vision-Instruct",
)

print(response.completion_message.content)

