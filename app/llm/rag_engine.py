# rag_engine.py
import os
import glob
import re
import ollama
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.core.config import load_system_prompt, LLM_MODEL, DOCS_DIR, TOP_K
from app.llm.date_parser import (
    detect_date_range_from_query,
    extract_date_from_path,
    get_today_context,
)
from app.llm.embeddings import embed_texts
from app.data.indexer import get_collection


def save_schedule_directly(date_str: str, content: str):
    """
    일정을 파일에 저장하는 함수
    """
    try:
        # 날짜 유효성 검사
        datetime.strptime(date_str, "%Y-%m-%d")
        
        filename = f"{date_str}.md"
        file_path = os.path.join(DOCS_DIR, filename)
        os.makedirs(DOCS_DIR, exist_ok=True)
        
        mode = "a" if os.path.exists(file_path) else "w"
        
        with open(file_path, mode, encoding="utf-8") as f:
            if mode == "a" and os.path.getsize(file_path) > 0:
                f.write("\n")
            
            if not content.strip().startswith("-"):
                content = f"- {content}"
                
            f.write(content)
            
        return True, file_path
        
    except ValueError:
        return False, f"날짜 형식이 잘못됨 ({date_str})"
    except Exception as e:
        return False, str(e)


def rag_query(query: str) -> str:
    """
    API 서버용으로 수정된 메인 함수.
    결과를 print하는 대신 문자열(str)로 return 합니다.
    """
    
    # 1) 프롬프트 준비
    today_iso, weekday = get_today_context()
    today_dt = datetime.strptime(today_iso, "%Y-%m-%d")
    tomorrow_iso = (today_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    idx = (4 - today_dt.weekday() + 7) % 7
    friday_iso = (today_dt + timedelta(days=idx)).strftime("%Y-%m-%d")

    base_prompt = load_system_prompt()
    filled_prompt = (
        base_prompt
        .replace("{{TODAY}}", today_iso)
        .replace("{{WEEKDAY}}", weekday)
        .replace("{{TOMORROW_DATE}}", tomorrow_iso)
        .replace("{{FRIDAY_DATE}}", friday_iso)
    )

    # 2) RAG 검색
    collection = get_collection()
    start_date, end_date = detect_date_range_from_query(query)
    
    valid_sources = []
    where = None

    if start_date and end_date:
        for path in glob.glob(os.path.join(DOCS_DIR, "*.*")):
            d = extract_date_from_path(path)
            if d and start_date <= d <= end_date:
                valid_sources.append(path)
        
        if valid_sources:
            where = {"source": {"$in": valid_sources}}

    docs_found = []
    metas = []
    try:
        q_emb = embed_texts([query])[0]
        result = collection.query(
            query_embeddings=[q_emb],
            n_results=TOP_K,
            where=where if valid_sources else None,
        )
        docs_found = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
    except:
        pass

    context_text = ""
    if docs_found:
        for i, (doc, meta) in enumerate(zip(docs_found, metas), start=1):
            src = os.path.basename(meta.get('source', 'unknown'))
            context_text += f"[{i}] (source: {src})\n{doc}\n\n"
    else:
        context_text = "(관련 문서 없음)"

    # 3) LLM 호출
    user_msg = f"""
[컨텍스트]
{context_text}

[사용자 입력]
"{query}"
"""

    print(f"\n[SERVER LOG] 사용자 질문: {query}")
    print("[SERVER LOG] AI 생성 중...")
    
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": filled_prompt},
            {"role": "user", "content": user_msg},
        ],
    )
    answer = response["message"]["content"].strip()

    # 4) 응답 분석 및 처리
    pattern = re.compile(r">>>\s*SAVE\s*[|:]?\s*(\d{4}-\d{2}-\d{2})\s*[|:]?\s*(.*)", re.DOTALL | re.IGNORECASE)
    match = pattern.search(answer)

    if match:
        # === [쓰기 모드] ===
        date_part = match.group(1)
        content_part = match.group(2).strip()
        content_part = content_part.lstrip("|: ").strip()

        print(f"[SERVER LOG] 저장 감지: {date_part} / {content_part}")
        
        success, msg = save_schedule_directly(date_part, content_part)
        
        if success:
            return f"✅ 일정을 등록했습니다!\n📅 날짜: {date_part}\n📝 내용: {content_part}"
        else:
            return f"❌ 저장 중 오류가 발생했습니다: {msg}"

    else:
        # === [읽기 모드] ===
        clean_answer = answer.replace("```json", "").replace("```", "").strip()
        return clean_answer