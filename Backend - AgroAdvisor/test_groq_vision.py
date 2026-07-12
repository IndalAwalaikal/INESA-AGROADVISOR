import asyncio
import os
import base64
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def test():
    # 1x1 transparent PNG
    dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
    try:
        completion = await groq_client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is in this image? Return JSON: {\"nama_hama\": \"...\"}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{dummy_b64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.2,
            max_tokens=1024,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"}
        )
        print("SUCCESS:", completion.choices[0].message.content)
    except Exception as e:
        print("FAILED:", e)

asyncio.run(test())
