import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")
print("loaded GEMINI_API_KEY:", os.getenv("GEMINI_API_KEY"))