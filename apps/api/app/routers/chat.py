# -*- coding: utf-8 -*-
from fastapi import APIRouter
from app.prompts import SYSTEM_PROMPT
from app.config import settings

# Utilise directement Chat Completions (plus simple que Responses)
from openai import OpenAI
client = OpenAI(api_key=settings.OPENAI_API_KEY)

router = APIRouter()

@router.post("/complete")
def complete(body: dict):
    q = (body.get("message") or "").strip()
    if not q:
        return {"reply": "(message vide)"}

    # Fallback local si pas de clé (ou si on veut juste tester le front)
    if not settings.OPENAI_API_KEY:
        return {"reply": f"[LOCAL MODE] Pong: {q}"}

    try:
        rsp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,  # gpt-4o / gpt-4o-mini ok ici
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
            ],
            temperature=0.3,
        )
        return {"reply": rsp.choices[0].message.content}
    except Exception as e:
        # Pas de 500 qui tue le front : on renvoie le texte d'erreur
        return {"reply": f"[ERROR LLM] {type(e).__name__}: {e}"}
