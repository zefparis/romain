from openai import OpenAI
from app.config import settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)
def embed_text(text: str) -> list[float]:
    e = client.embeddings.create(model=settings.EMBED_MODEL, input=text)
    return e.data[0].embedding
