from fastapi import APIRouter
from app.prompts import SYSTEM_PROMPT
from app.llm import llm_respond
router = APIRouter()
@router.post("/complete")
def complete(body: dict):
    q = body.get("message", "")
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": q}
    ]
    tools = [{
        "type": "function",
        "function": {
            "name": "export_document",
            "description": "Génère un document (pdf|docx|xlsx) à partir d’un payload.",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {"type": "string", "enum": ["pdf","docx","xlsx"]},
                    "template_id": {"type": "string"},
                    "data": {"type": "object"}
                },
                "required": ["format","data"]
            }
        }
    }]
    out = llm_respond(msgs, tools=tools)
    return {"reply": out}
