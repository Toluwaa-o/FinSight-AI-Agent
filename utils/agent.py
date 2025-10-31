import os
from .utils import chat
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
base_url = os.getenv("BASE_URL")
model = os.getenv('MODEL')

client = OpenAI(
    api_key=GOOGLE_API_KEY,
    base_url=base_url
)


def call_agent(input: str) -> str:
    history = []

    try:
        response = chat(client, model, input, history)
        return response
    except Exception as e:
        return {"error": str(e)}
