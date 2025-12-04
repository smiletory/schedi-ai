# schedi-ai
**Schedi AI**는 날짜 기반 문서를 자동으로 인덱싱하고,  
자연어 질문을 분석하여 해당 날짜 문서를 기반으로 응답하는  
**로컬 RAG(Retrieval-Augmented Generation) 엔진**입니다.

- 자연어 날짜 파싱  
- ChromaDB 벡터 검색  
- Ollama 기반 로컬 LLM  
- 문서 기반 답변 생성  
- CLI 테스트 가능  

---

## ⚙️ 개발환경 세팅

### 1️. Ollama 설치
https://ollama.com/download

### 2️. 저장소 클론
```bash
git clone https://github.com/smiletory/schedi-ai.git
cd schedi-ai
```

### 3. setup.bat 파일 실행
```bash
.\setup.bat
```

### 4. 가상환경 활성화

**Windows**
```bash
.venv\Scripts\activate
```

**macOS / Linux**
```bash
source .venv/bin/activate
```
---

## ▶️ 실행환경

### 실행
```bash
python main.py
```

### 예시 입력
```
질문 (quit 종료): 다음주 할 일 뭐야?
```

### 문서 추가
`docs/` 폴더에 Markdown 문서를 추가하면 자동 인덱싱됨.

예:
```
docs/2025-11-27.md
```

예시 내용:
```markdown
# 2025-11-27 일정
- 10:00 회의
- 14:00 알고리즘 공부
- 저녁 약속
```

---

## 🧠 RAG 작동 흐름

1. 문서 로드  
2. Chunk 단위 분리  
3. 임베딩 생성  
4. ChromaDB 저장  
5. 사용자 쿼리에서 날짜 범위 인식  
6. 해당 날짜 문서만 벡터 검색  
7. 관련 문서를 기반으로 LLM 응답 생성  

---

## 📝 LLM 모델 커스터마이징

LLM 말투·지침은 아래 파일에서 수정:

```
prompts/system_prompt.txt
```

---


## 📁 프로젝트 폴더 구조

```plaintext
schedi-ai/
 ├ .venv/                 # Python 가상환경
 ├ .vscode/               # VS Code 설정
 ├ app/                   # AI 엔진 핵심 코드
 │   ├ core/
 │   │   └ config.py      # 설정 & 경로 관리
 │   ├ data/
 │   │   ├ indexer.py       # 문서 인덱싱 / Chroma 컬렉션 관리
 │   │   └ text_splitter.py # Chunk 단위 문서 분리
 │   ├ llm/
 │   │   ├ date_parser.py # 자연어 날짜 파서
 │   │   ├ embeddings.py  # 텍스트 → 벡터 변환
 │   │   └ rag_engine.py  # RAG 파이프라인
 ├ chroma_data/           # ChromaDB 벡터 저장소 (Git 미포함)
 ├ docs/                  # 일정 문서 (YYYY-MM-DD.md)
 ├ prompts/
 │   └ system_prompt.txt  # 시스템 프롬프트
 ├ main.py                # CLI 실행 엔트리포인트
 └ README.md
```
