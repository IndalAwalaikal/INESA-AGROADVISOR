import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
if not key:
    print("CRITICAL: GEMINI_API_KEY is not set!")
    exit(1)

client = genai.Client(api_key=key)

print(f"Listing models for key ...{key[-4:]}")
try:
    # list() is a generator/iterator
    count = 0
    for m in client.models.list():
        count += 1
        print(f"-> Name: {m.name}")
        print(f"   Display Name: {m.display_name}")
        print(f"   Supported Methods: {m.supported_generation_methods}")
    if count == 0:
        print("No models returned by list().")
except Exception as e:
    print(f"Error listing models: {e}")

# Try a direct test of a known model if list() fails
print("\nVerifying 'gemini-1.5-flash' specifically...")
try:
    client.models.get(model='gemini-1.5-flash')
    print("Model 'gemini-1.5-flash' found!")
except Exception as e:
    print(f"Model 'gemini-1.5-flash' NOT found: {e}")
