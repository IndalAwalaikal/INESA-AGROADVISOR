import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS_TO_TEST = [
    'gemini-2.5-flash-lite',
    'gemini-flash-latest',
    'groq/llama-3.3-70b-versatile'
]

prompt = "Hello, respond with 'OK' and your model name if you receive this."

# Groq setup
from groq import AsyncGroq
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

import asyncio

async def test_all():
    for model_name in MODELS_TO_TEST:
        print(f"Testing model: {model_name}...")
        try:
            if model_name.startswith("groq/"):
                m_real = model_name.split("/", 1)[1]
                response = await groq_client.chat.completions.create(
                    model=m_real,
                    messages=[{"role": "user", "content": prompt}]
                )
                print(f"SUCCESS! -> {response.choices[0].message.content.strip()}")
            else:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                print(f"SUCCESS! -> {response.text.strip()}")
        except Exception as e:
            print(f"FAILED: {e}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_all())
