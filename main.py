# main.py
from app.data.indexer import build_index
from app.llm.rag_engine import rag_query


def main():
    print("[MAIN] 인덱싱 생성 중...")
    build_index()

    while True:
        q = input("\n질문 (quit 종료): ")
        if q.lower() in ("quit", "exit", "q"):
            break
        rag_query(q)


if __name__ == "__main__":
    main()
