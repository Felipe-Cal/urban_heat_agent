#!/bin/bash
# Railway start script for Streamlit

# Ensure PORT is set (Railway sets it, but fallback for safety)
if [ -z "$PORT" ]; then
    export PORT=8501
fi

# Detect python executable
if [ -f "/app/.venv/bin/python" ]; then
    PYTHON_CMD="/app/.venv/bin/python"
else
    PYTHON_CMD="python"
fi

echo "Starting Streamlit on port $PORT using $PYTHON_CMD..."
$PYTHON_CMD -m streamlit run app.py --server.port $PORT --server.address 0.0.0.0
