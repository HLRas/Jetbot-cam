#!/bin/bash
# Jetson Camera Launcher
# Uses system Python 3.6.9 with working OpenCV 3.2.0

echo "🎥 Starting Jetson Nano Camera Stream"
echo "Using System Python 3.6.9 + OpenCV 3.2.0"
echo "=================================="

# Navigate to script directory
cd "$(dirname "$0")"

# Run with system Python
/usr/bin/python3 working_camera_stream.py
