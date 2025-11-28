# embeddings.py
import ollama
from app.core.config import EMBED_MODEL


def embed_texts(texts):
    vectors = []
    for t in texts:
        resp = ollama.embeddings(model=EMBED_MODEL, prompt=t)
        vectors.append(resp["embedding"])
    return vectors
