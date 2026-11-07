import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
_client = None


def client():
    global _client
    if _client is None:
        from groq import Groq
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is missing. Copy .env.example to .env and add your key.")
        _client = Groq(api_key=key)
    return _client
