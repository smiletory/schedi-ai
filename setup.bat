@echo off
chcp 65001 > nul
echo.

echo [1] 가상환경 확인 중...

:: .venv 존재 + 내부 python.exe 확인
if not exist .venv\Scripts\python.exe (
    echo 가상환경이 없거나 손상됨 → 새로 생성합니다.
    python -m venv .venv
) else (
    echo 가상환경이 이미 존재합니다.
)

echo.
echo [2] pip 및 라이브러리 설치 중...

.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo [3] Ollama 모델 확인 및 다운로드...

:: Gemma 3 1B
ollama list | findstr /i "gemma3:1b" > nul
if errorlevel 1 (
    echo gemma3:1b 모델이 없어 pull 합니다...
    ollama pull gemma3:1b
) else (
    echo gemma3:1b 모델이 이미 설치됨.
)

:: EmbeddingGemma
ollama list | findstr /i "embeddinggemma" > nul
if errorlevel 1 (
    echo embeddinggemma 모델이 없어 pull 합니다...
    ollama pull embeddinggemma
) else (
    echo embeddinggemma 모델이 이미 설치됨.
)

echo.
echo --------------------------------
echo [완료] 개발 환경 초기화 완료!
echo --------------------------------
pause
