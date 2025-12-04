@echo off
chcp 65001 > nul
echo.

:: 1. 가상환경 폴더(.venv) 확인(없으면 생성)
if not exist .venv (
    python -m venv .venv
)

:: 2. 가상환경 내 라이브러리 설치
echo.
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

:: 3. Ollama 모델 다운로드
echo.
ollama pull gemma3:1b
ollama pull embeddinggemma

echo.
echo [완료]
pause
