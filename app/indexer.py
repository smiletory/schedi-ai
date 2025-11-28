# indexer.py
import glob
import os
import chromadb

from app.text_splitter import split_text
from app.embeddings import embed_texts
from app.config import DOCS_DIR, CHROMA_DIR, COLLECTION_NAME, CHUNK_SIZE, CHUNK_OVERLAP


_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def get_collection():
    return _collection


def build_index():
    global _collection

    print("[INDEX] 기존 컬렉션 삭제 후 재생성")
    try:
        _client.delete_collection(COLLECTION_NAME)
    except:
        pass

    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    docs = []
    metadatas = []
    ids = []

    file_paths = glob.glob(os.path.join(DOCS_DIR, "*.*"))
    print("[DEBUG] 인덱싱 대상:", file_paths)

    doc_id = 0

    for path in file_paths:
        if not path.lower().endswith((".txt", ".md")):
            continue

        print(f"[DEBUG] 처리 중: {path}")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        chunks = split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)

        for chunk in chunks:
            docs.append(chunk)
            metadatas.append({"source": path})
            ids.append(f"doc_{doc_id}")
            doc_id += 1

    if docs:
        vectors = embed_texts(docs)
        _collection.add(
            documents=docs,
            embeddings=vectors,
            metadatas=metadatas,
            ids=ids,
        )

    print("[INDEX] 완료!")
