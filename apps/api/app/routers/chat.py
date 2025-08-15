# -*- coding: utf-8 -*-
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, constr
from app.prompts import SYSTEM_PROMPT
from app.config import settings

# Utilise directement Chat Completions (plus simple que Responses)
from openai import OpenAI
client = OpenAI(api_key=settings.OPENAI_API_KEY)

router = APIRouter()
logger = logging.getLogger("app")


class ChatRequest(BaseModel):
    message: constr(strip_whitespace=True, min_length=1)


class ChatResponse(BaseModel):
    reply: str

@router.post("/complete", response_model=ChatResponse)
def complete(payload: ChatRequest, request: Request):
    q = payload.message
    logger.info({"event": "chat_complete", "message": q})

    # Fallback local si pas de clé (ou si on veut juste tester le front)
    if not settings.OPENAI_API_KEY:
        return ChatResponse(reply=f"[LOCAL MODE] Pong: {q}")

    try:
        rsp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,  # gpt-4o / gpt-4o-mini ok ici
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
            ],
            temperature=0.3,
        )
        return ChatResponse(reply=rsp.choices[0].message.content)
    except Exception as e:
        logger.exception("chat_complete failed")
        return JSONResponse(status_code=500, content={"detail": f"LLM error: {type(e).__name__}"})

@router.post("/complete/stream")
def complete_stream(body: dict):
    """Renvoie une réponse en streaming SSE (text/event-stream).
    Format: lignes "data: <chunk>\n\n" et "data: [DONE]\n\n" à la fin.
    """
    q = (body.get("message") or "").strip()
    if not q:
        def gen_empty():
            yield "data: (message vide)\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(gen_empty(), media_type="text/event-stream")

    def event_stream():
        # Local fallback (pas de clé): simule un streaming mot à mot
        if not settings.OPENAI_API_KEY:
            import time
            text = f"[LOCAL MODE] Pong: {q}"
            for word in text.split(" "):
                yield f"data: {word} " + "\n\n"
                time.sleep(0.02)
            yield "data: [DONE]\n\n"
            return

        try:
            rsp = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": q},
                ],
                temperature=0.3,
                stream=True,
            )
            for chunk in rsp:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    # SSE frame
                    yield f"data: {delta}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {type(e).__name__}: {e}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
