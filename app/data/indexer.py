# indexer.py
import glob
import os
import time
import chromadb
from typing import Dict, List

from app.data.text_splitter import split_text
from app.llm.embeddings import embed_texts
from app.core.config import DOCS_DIR, CHROMA_DIR, COLLECTION_NAME, CHUNK_SIZE, CHUNK_OVERLAP

# ChromaDB 클라이언트 설정 (변경 없음)
_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

def get_collection():
    return _collection

def build_index():
    """
    증분 인덱싱(Incremental Indexing) 구현:
    - DB에 없는 새 파일 -> 추가
    - 내용이 변경된 파일 -> 기존 거 지우고 다시 추가
    - 삭제된 파일 -> DB에서 제거
    - 변경 없는 파일 -> 건너뜀 (속도 향상 핵심!)
    """
    global _collection
    
    print(f"[INDEX] 인덱싱 점검 시작 ({DOCS_DIR})")
    
    # 1. 현재 DB에 저장된 파일 정보 가져오기 (source -> last_modified 매핑)
    #    주의: 문서가 많아지면 limit을 늘리거나 페이지네이션이 필요할 수 있음
    existing_data = _collection.get(include=["metadatas"])
    db_file_map: Dict[str, float] = {}
    
    if existing_data and existing_data["metadatas"]:
        for meta in existing_data["metadatas"]:
            # 메타데이터에 'last_modified'가 없으면(구버전 데이터) 0으로 처리하여 강제 업데이트 유도
            source = meta.get("source")
            last_mod = meta.get("last_modified", 0.0)
            db_file_map[source] = last_mod

    # 2. 디스크의 실제 파일 목록 스캔
    disk_files = glob.glob(os.path.join(DOCS_DIR, "*.*"))
    valid_disk_files = [f for f in disk_files if f.lower().endswith((".txt", ".md"))]
    
    files_to_add = []
    sources_to_delete = set()
    
    # 3. 변경 사항 감지 로직
    for path in valid_disk_files:
        try:
            current_mtime = os.path.getmtime(path)
        except OSError:
            continue # 파일 접근 불가 시 스킵

        # Case A: DB에 없는 새 파일
        if path not in db_file_map:
            print(f"[+] 새 파일 발견: {os.path.basename(path)}")
            files_to_add.append(path)
            
        # Case B: DB에 있지만 수정된 파일 (mtime 비교)
        elif current_mtime > db_file_map[path]:
            print(f"[*] 변경된 파일: {os.path.basename(path)}")
            sources_to_delete.add(path) # 기존 데이터 삭제 예약
            files_to_add.append(path)   # 재추가 예약
            
        # Case C: 변경 없음 (건너뜀)
        else:
            # print(f"[-] 변경 없음: {os.path.basename(path)}") # 너무 시끄러우면 주석 처리
            pass

    # Case D: 디스크에서 삭제된 파일 감지
    disk_file_set = set(valid_disk_files)
    for db_source in db_file_map.keys():
        if db_source not in disk_file_set:
            print(f"[-] 삭제된 파일 정리: {os.path.basename(db_source)}")
            sources_to_delete.add(db_source)

    # 4. DB 업데이트 실행
    
    # (1) 삭제할 문서 처리
    if sources_to_delete:
        print(f"[INDEX] {len(sources_to_delete)}개 파일의 기존 데이터 삭제 중...")
        # where 필터를 사용해 해당 소스의 모든 청크 삭제
        _collection.delete(where={"source": {"$in": list(sources_to_delete)}})

    # (2) 추가/업데이트할 문서 처리
    if files_to_add:
        print(f"[INDEX] {len(files_to_add)}개 파일 임베딩 및 추가 중...")
        new_docs = []
        new_metas = []
        new_ids = []
        
        doc_counter = int(time.time()) # ID 충돌 방지용 타임스탬프

        for path in files_to_add:
            try:
                current_mtime = os.path.getmtime(path)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                
                chunks = split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
                
                for i, chunk in enumerate(chunks):
                    new_docs.append(chunk)
                    # 메타데이터에 mtime 저장 (다음 비교를 위해 필수)
                    new_metas.append({
                        "source": path,
                        "last_modified": current_mtime
                    })
                    new_ids.append(f"doc_{doc_counter}_{i}")
                
                doc_counter += 1
                
            except Exception as e:
                print(f"[ERROR] 파일 처리 실패 ({path}): {e}")

        # 일괄 삽입 (Batch Insert)
        if new_docs:
            vectors = embed_texts(new_docs)
            _collection.add(
                documents=new_docs,
                embeddings=vectors,
                metadatas=new_metas,
                ids=new_ids,
            )
            print(f"[INDEX] {len(new_docs)}개 청크 추가 완료.")
    
    if not files_to_add and not sources_to_delete:
        print("[INDEX] 변경 사항 없음. 최신 상태입니다.")
    else:
        print("[INDEX] 동기화 완료!")