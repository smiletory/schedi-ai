# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import sys
import os

# 모듈 경로 추가 (app 패키지를 찾기 위해)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.data.indexer import build_index
from app.llm.rag_engine import rag_query

# 1. FastAPI 앱 초기화
app = FastAPI(
    title="Schedi-AI Backend",
    description="LLM 기반 일정 관리 어시스턴트 API",
    version="1.0.0"
)

# 2. 데이터 모델 정의 (요청/응답 형식)
class ChatRequest(BaseModel):
    message: str  # 사용자가 보낼 메시지

class ChatResponse(BaseModel):
    response: str # AI가 보낼 응답

# 3. 서버 시작 시 실행될 이벤트
@app.on_event("startup")
async def startup_event():
    print("🚀 서버 시작! 데이터 인덱싱을 점검합니다...")
    build_index() # 서버 켤 때 인덱싱 한 번 돌리기

# 4. API 엔드포인트 (POST /chat)
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    사용자의 메시지를 받아 AI의 답변을 반환합니다.
    """
    user_query = request.message
    
    if not user_query:
        raise HTTPException(status_code=400, detail="메시지가 비어있습니다.")
    
    try:
        # RAG 엔진 호출
        ai_answer = rag_query(user_query)
        return ChatResponse(response=ai_answer)
    
    except Exception as e:
        print(f"[ERROR] 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 5. 로컬 테스트용 실행 코드
if __name__ == "__main__":
    # 터미널에서 `python server.py`로 실행 가능
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)