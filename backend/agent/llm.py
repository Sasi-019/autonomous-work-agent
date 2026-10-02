import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


load_dotenv()


HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL")


if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN is missing from the environment."
    )


if not HF_MODEL:
    raise RuntimeError(
        "HF_MODEL is missing from the environment."
    )


client = InferenceClient(
    token=HF_TOKEN
)


def ask_llm(prompt: str):
    response = client.chat.completions.create(
        model=HF_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1000
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "LLM returned no text content."
        )

    return content