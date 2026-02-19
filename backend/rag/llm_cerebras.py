import os
import requests

CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

if not CEREBRAS_API_KEY:
    raise RuntimeError("CEREBRAS_API_KEY not set")

CEREBRAS_API_URL = "https://api.cerebras.ai/v1/completions"

HEADERS = {
    "Authorization": f"Bearer {CEREBRAS_API_KEY}",
    "Content-Type": "application/json",
}


def generate_answer(system_prompt: str, user_prompt: str) -> str:
    """
    Cerebras completion API (correct schema)
    """

    full_prompt = (
        f"{system_prompt}\n\n"
        f"{user_prompt}\n\n"
        "Answer:"
    )

    payload = {
        "model": "llama3.1-8b",     # ✅ confirmed supported
        "prompt": full_prompt,
        "max_tokens": 256,
        "temperature": 0.2,
        "top_p": 0.9,
        "stream": False            # ✅ IMPORTANT
    }

    response = requests.post(
        CEREBRAS_API_URL,
        headers=HEADERS,
        json=payload,
        timeout=60
    )

    # 🔍 Debug if it fails again
    if response.status_code != 200:
        raise RuntimeError(
            f"Cerebras API error {response.status_code}: {response.text}"
        )

    data = response.json()
    return data["choices"][0]["text"].strip()
