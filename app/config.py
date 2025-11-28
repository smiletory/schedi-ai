# app/config.py
import os

# ===== 디렉토리 계산 =====
APP_DIR = os.path.dirname(os.path.abspath(__file__))     # app 폴더
BASE_DIR = os.path.dirname(APP_DIR)                      # 프로젝트 루트

# ===== 경로 설정 =====
DOCS_DIR = os.path.join(BASE_DIR, "docs")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_data")
PROMPT_FILE = os.path.join(BASE_DIR, "prompts", "system_prompt.txt")

# ===== 모델 =====
EMBED_MODEL = "embeddinggemma"
LLM_MODEL = "gemma3:1b"

# ===== 기타 =====
COLLECTION_NAME = "local_docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K = 4


# ===== 시스템 프롬프트 로드 =====
def load_system_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()
