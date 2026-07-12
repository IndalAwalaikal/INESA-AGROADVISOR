import asyncio
from app.services.pestisida_ai_service import identifikasi_hama_dari_gambar
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    print("Testing image AI fix...")
    # read real image if exists, else dummy bytes that is valid base64
    try:
        with open("not_exists.jpg", "rb") as f:
            b = f.read()
    except Exception:
         # Use a 1x1 transparent PNG as fake data to prevent gemini API rejecting completely garbage bytes
         b = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
         
    res = await identifikasi_hama_dari_gambar(b, "image/png")
    print(res)

asyncio.run(test())
