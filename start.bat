@echo off
REM Windows batch script to start OmniKnowledgeBase

echo Starting OmniKnowledgeBase...
echo.

echo [1/2] Starting FastAPI backend...
start "OmniKnowledgeBase Backend" cmd /k "python -m uvicorn backend.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Streamlit frontend...
start "OmniKnowledgeBase Frontend" cmd /k "cd frontend && streamlit run app.py"

echo.
echo Both services are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8501
echo.
echo Press any key to exit this window (services will continue running)...
pause >nul

