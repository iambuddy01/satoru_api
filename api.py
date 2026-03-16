from fastapi import FastAPI
from pydantic import BaseModel
import requests

from config import CEREBRAS_API_KEY, MODEL_NAME, CEREBRAS_ENDPOINT
from satoru_prompt import SYSTEM_PROMPT


app = FastAPI(
    title="Satoru AI API",
    version="1.0"
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {"status": "Satoru AI running"}


@app.post("/chat")
async def chat(req: ChatRequest):

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": req.message}
        ],
        "temperature": 0.9,
        "max_tokens": 800
    }

    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        CEREBRAS_ENDPOINT,
        headers=headers,
        json=payload
    )

    data = response.json()

    reply = data["choices"][0]["message"]["content"]

    return {
        "reply": reply
    }
