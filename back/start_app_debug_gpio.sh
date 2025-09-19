#!/bin/bash

# Start TheOpenMusicBox with debug logging for GPIO
# This script enables debug logging to see GPIO events

echo "🔍 Starting TheOpenMusicBox with GPIO debug logging..."
echo "Press Ctrl+C to stop"

# Set environment variables for debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG
export ENABLE_PERFORMANCE_MONITORING=true
export ENABLE_EVENT_MONITORING=true

# Start the application
python3 -m uvicorn app.main:app_sio --host 127.0.0.1 --port 5005 --log-level debug