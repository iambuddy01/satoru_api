from fastapi import FastAPI, Request
from pydantic import BaseModel
import aiohttp
from collections import defaultdict, deque

from config import CEREBRAS_API_KEY, MODEL_NAME, CEREBRAS_ENDPOINT
from satoru_prompt import SYSTEM_PROMPT


app = FastAPI(
    title="Satoru AI API",
    version="2.4"
)


# -----------------------
# Memory (last 10 msgs)
# -----------------------
memory = defaultdict(lambda: deque(maxlen=10))


# -----------------------
# Emoji Intelligence
# -----------------------
emoji_map = {
    "😂": "user laughing",
    "🤣": "user laughing hard",
    "😡": "user angry",
    "😏": "user teasing",
    "❤️": "user affection",
    "🔥": "user excited",
    "😭": "user crying"
}


# -----------------------
# Insult Detection
# -----------------------
insult_words = [
    "madarchod","bhosdike","chutiya","lode","bc","mc",
    "fuck","bitch","asshole","idiot","loser"
]


# -----------------------
# Flirt Detection
# -----------------------
flirt_words = [
    "hi","hello","hey","hii","sup",
    "kaise ho","kya kar rahe ho","hello baby","hey baby"
]


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/")
async def home():
    return {"status": "Satoru AI running"}


@app.post("/chat")
async def chat(req: ChatRequest, request: Request):

    user_text = req.message

    # talk.py compatible session
    session = req.session_id or request.client.host


    # -----------------------
    # Emoji Intelligence
    # -----------------------
    for emoji, meaning in emoji_map.items():
        if emoji in user_text:
            user_text += f" (emotion: {meaning})"


    # -----------------------
    # Ultra Roast Trigger
    # -----------------------
    if any(word in user_text.lower() for word in insult_words):

        user_text = f"""
User insulted you saying: "{user_text}"

Activate ULTRA ROAST MODE.

Destroy the insult with an extremely savage witty comeback.
Make the user look stupid.
Reply must stay under 2–3 lines.
"""


    # -----------------------
    # Flirt Trigger
    # -----------------------
    elif any(word in user_text.lower() for word in flirt_words):

        user_text = f"""
User greeted you: "{user_text}"

Reply with confident playful flirt energy.
Keep reply short (1–2 sentences).
"""


    # -----------------------
    # Conversation Memory
    # -----------------------
    history = list(memory[session])

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_text}
    ]


    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.85,
        "max_tokens": 80,
        "top_p": 0.9
    }


    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json"
    }


    try:

        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(
                CEREBRAS_ENDPOINT,
                headers=headers,
                json=payload
            ) as response:

                data = await response.json()

                reply = data["choices"][0]["message"]["content"].strip()


                # -----------------------
                # Reply Cleaning
                # -----------------------
                reply = reply.replace("```", "").strip()

                if reply.startswith('"') and reply.endswith('"'):
                    reply = reply[1:-1]

                if not reply:
                    reply = "Kya hua bhai 😏 bol."


                # -----------------------
                # Save Memory
                # -----------------------
                memory[session].append({"role": "user", "content": req.message})
                memory[session].append({"role": "assistant", "content": reply})


                return {"reply": reply}


    except Exception:
        return {"reply": "😅 Net thoda slow ho gaya… phir bol."}
