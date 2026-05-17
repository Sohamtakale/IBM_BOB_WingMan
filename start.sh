#!/bin/bash
# WingMan startup script

echo "🪽 Starting WingMan..."

# Backend
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt -q

echo ""
echo "⚠️  IMPORTANT: Twilio needs a public URL to reach your backend."
echo "   If running locally, open another terminal and run:"
echo "   ngrok http 8000"
echo "   Then update BASE_URL in .env with your ngrok https URL."
echo ""

# Start backend
echo "Starting backend on http://localhost:8000 ..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
cd frontend
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

echo "Starting frontend on http://localhost:5173 ..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ WingMan running!"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
