from huggingface_hub import InferenceClient
import os

client = InferenceClient(
    provider="hf-inference",   # explicitly force router
    token=os.getenv("HUGGINGFACE_TOKEN")
)

try:
    response = client.text_generation(
        model="google/gemma-2b-it",
        prompt="Explain cybersecurity in one sentence.",
        max_new_tokens=50,
    )

    print("SUCCESS:")
    print(response)

except Exception as e:
    print("FAILED:")
    print(type(e).__name__)
    print(e)