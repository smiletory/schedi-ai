# rag_engine.py
import os
import glob
import ollama

from app.config import load_system_prompt, LLM_MODEL, DOCS_DIR, TOP_K
from app.date_parser import detect_date_range_from_query, extract_date_from_path, get_today_context
from app.embeddings import embed_texts
from app.indexer import get_collection



def rag_query(query: str):
    collection = get_collection()

    # 1) 날짜 파싱
    start_date, end_date = detect_date_range_from_query(query)
    date_filter = start_date is not None and end_date is not None

    valid_sources = None

    # 2) 날짜 기반 파일 필터링
    if date_filter:
        valid_sources = []
        for path in glob.glob(os.path.join(DOCS_DIR, "*.*")):
            d = extract_date_from_path(path)
            if d and start_date <= d <= end_date:
                valid_sources.append(path)

    # 3) 파일 없음 → LLM 안내 메시지
    if date_filter and not valid_sources:
        today_iso, weekday = get_today_context()
        system_prompt = load_system_prompt().replace("{{TODAY}}", today_iso).replace("{{WEEKDAY}}", weekday)

        user_message = f"""
사용자 질문: "{query}"
해석된 날짜 범위: {start_date} ~ {end_date}

해당 기간에 문서가 없습니다. 이를 자연스럽게 설명해 주세요.
"""

        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )

        print("\n===== 답변 =====\n")
        print(response["message"]["content"])
        print("\n================")
        return

    # 4) where 필터 구성
    where = None
    if date_filter:
        where = {"source": {"$in": valid_sources}}

    # 5) 쿼리 임베딩
    q_emb = embed_texts([query])[0]

    # 6) 벡터 검색
    result = collection.query(
        query_embeddings=[q_emb],
        n_results=TOP_K,
        where=where,
    )

    docs_found = result["documents"][0]
    metas = result["metadatas"][0]

    if not docs_found:
        print("[RAG] 검색 결과 없음")
        return

    # 7) 컨텍스트 구성
    context = ""
    for i, (doc, meta) in enumerate(zip(docs_found, metas), start=1):
        context += f"[{i}] (source: {meta.get('source')})\n{doc}\n\n"

    # 8) LLM 호출
    today_iso, weekday = get_today_context()
    system_prompt = load_system_prompt().replace("{{TODAY}}", today_iso).replace("{{WEEKDAY}}", weekday)

    user_msg = f"""
아래는 질문과 관련된 문서들입니다:

{context}

질문: {query}

위 문서를 참고하여 한국어로 자연스럽게 답변해 주세요.
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    )

    print("\n===== 답변 =====\n")
    print(response["message"]["content"])
    print("\n================")
