# -*- coding: utf-8 -*-
from openai import OpenAI
from app.config import settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)
def llm_respond(messages: list, tools: list | None = None) -> str:
    rsp = client.responses.create(model=settings.OPENAI_MODEL, input=messages, tools=tools or [], temperature=0.3)
    return rsp.output_text
