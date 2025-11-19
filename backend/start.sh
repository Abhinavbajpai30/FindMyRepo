#!/bin/bash
set -e

# Railway provides PORT env (default 8080), fallback to 8080 if not set
PORT=${PORT:-8080}

echo "Starting FastAPI server on port $PORT"

# Use a single worker for lightweight apps (scale via Railway dynos instead of threads)
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers 1
