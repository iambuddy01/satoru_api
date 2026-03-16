from fastapi import FastAPI, Request
from pydantic import BaseModel
import aiohttp
from collections import defaultdict, deque

from config import CEREBRAS_API_KEY, MODEL_NAME, CEREBRAS_ENDPOINT
from satoru_prompt import SYSTEM_PROMPT


app = FastAPI(
    title="Satoru AI API",
    version="3.1"
)


# -----------------------
# Memory
# -----------------------
memory = defaultdict(lambda: deque(maxlen=12))


# -----------------------
# Emoji Intelligence
# -----------------------
emoji_map = {
    "😂": "user laughing",
    "🤣": "user laughing hard",
    "😡": "user angry",
    "😏": "user teasing",
    "🔥": "user excited",
    "😭": "user crying",
}


# -----------------------
# Insult Severity Levels
# -----------------------
light_insults = [
    "idiot","noob","loser","stupid"
]

medium_insults = [
    "chutiya","bhosdike","lode","bc","mc"
]

extreme_insults = [
    "madarchod","fuck","bitch","asshole"
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

    session = req.session_id or request.client.host


    # -----------------------
    # Emoji Intelligence
    # -----------------------
    for emoji, meaning in emoji_map.items():
        if emoji in user_text:
            user_text += f" (emotion: {meaning})"


    lower = user_text.lower()


    # -----------------------
    # Insult Severity Detection
    # -----------------------
    if any(word in lower for word in extreme_insults):

        user_text = f"""
User used extremely abusive language: "{user_text}"

Activate EXTREME ROAST MODE.

Respond with multi-layer savage roasting.
Destroy the user's confidence.
Reply must stay under 2-3 lines.
"""

    elif any(word in lower for word in medium_insults):

        user_text = f"""
User insulted you: "{user_text}"

Activate STRONG ROAST MODE.

Respond with a sarcastic and humiliating comeback.
Keep reply short.
"""

    elif any(word in lower for word in light_insults):

        user_text = f"""
User mocked you: "{user_text}"

Respond with playful witty roast.
Make them look slightly dumb but keep it funny.
"""


    # -----------------------
    # Flirt Trigger
    # -----------------------
    elif any(word in lower for word in flirt_words):

        user_text = f"""
User greeted you: "{user_text}"

Respond with confident playful flirting.
Keep reply short (1-2 sentences).
"""


    # -----------------------
    # Group Roast Mode
    # -----------------------
    if len(memory[session]) >= 2:

        last_msg = memory[session][-2]["content"]

        if "bot" in last_msg.lower():

            user_text += """

Multiple users are mocking you in a group chat.

Activate GROUP ROAST MODE.
Roast them collectively with sarcastic humor.
Keep reply short but impactful.
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

                reply = reply.strip()

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
