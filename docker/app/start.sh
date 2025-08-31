#!/bin/bash

# Set default environment variables if not provided
export OLLAMA_HOST=${OLLAMA_HOST:-ollama}
export OLLAMA_PORT=${OLLAMA_PORT:-11434}
export OLLAMA_BASE_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"

echo "Starting AI Chat Application..."
echo "Ollama URL: ${OLLAMA_BASE_URL}"

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
while ! curl -s "${OLLAMA_BASE_URL}/api/tags" > /dev/null; do
    echo "Waiting for Ollama API at ${OLLAMA_BASE_URL}..."
    sleep 5
done
echo "Ollama is ready!"

# Start the backend server
echo "Starting backend server..."
cd /app/backend
python -m backend &

# Wait a moment for backend to start
sleep 5

# Serve the frontend (simple HTTP server)
echo "Starting frontend server..."
cd /app/frontend/build
python -m http.server 3000 &

echo "Application started successfully!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"

# Keep the container running
wait
