#!/bin/bash
# Linux/Mac script to start OmniKnowledgeBase

echo "Starting OmniKnowledgeBase..."
echo ""

echo "[1/2] Starting FastAPI backend..."
python -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

sleep 3

echo "[2/2] Starting Streamlit frontend..."
cd frontend
streamlit run app.py &
FRONTEND_PID=$!
cd ..

echo ""
echo "Both services are starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8501"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop both services..."

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait

