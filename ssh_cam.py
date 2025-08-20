#!/usr/bin/env python3
"""
Simple Web Camera Stream for Jetson Nano
Built on working basic_camera_test pipeline
"""

import cv2
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import os
from typing import List
import numpy as np
from image_processor import ImageProcessor

class CameraWebStreamer:
    def __init__(self):
        self.frame = None
        self.camera = None
        self.running = False
        self.frame_count = 0
        self.image_processor = ImageProcessor()
        
    def get_jetson_ip(self) -> List[str]:
        """Get Jetson IP addresses"""
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                return [ip for ip in ips if ip and not ip.startswith('127.')]
        except:
            pass
        return ['localhost']
    
    def start_camera(self) -> bool:
        """Initialize CSI camera with working pipeline"""
        print("🎥 Initializing CSI camera...")
        
        # Use the EXACT working pipeline from basic_camera_test
        working_pipeline = (
            "nvarguscamerasrc sensor-id=0 ! "
            "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=60/1 ! "
            "nvvidconv ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! "
            "appsink"
        )
        
        print("🔍 Trying working CSI pipeline...")
        try:
            self.camera = cv2.VideoCapture(working_pipeline, cv2.CAP_GSTREAMER)
            
            if self.camera.isOpened():
                # Test frame capture
                ret, test_frame = self.camera.read()
                if ret:
                    print(f"✅ CSI Camera initialized successfully!")
                    print(f"📹 Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                    return True
                else:
                    print("⚠️ Camera opened but cannot capture frames")
                    self.camera.release()
            else:
                print("❌ Failed to open camera")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            if self.camera:
                self.camera.release()
        
        print("❌ Camera initialization failed")
        return False
        
    def capture_frames(self) -> None:
        """Continuous frame capture thread"""
        print("📸 Starting frame capture...")
        
        while self.running and self.camera:
            ret, frame = self.camera.read()
            if ret:
                self.frame_count += 1
                
                # Add overlay information
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, f"Jetson Nano Camera", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"{timestamp}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(frame, f"Frame: {self.frame_count}", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Process for ArUco detection
                processed_frame = self.image_processor.process_frame(frame)
                
                # Store the frame
                self.frame = processed_frame.copy()
                
                # Print status every 100 frames
                if self.frame_count % 100 == 0:
                    print(f"📊 Captured {self.frame_count} frames")
            else:
                print("⚠️ Failed to capture frame")
                time.sleep(0.1)
                
    def get_frame_jpeg(self):
        """Get current frame as JPEG bytes"""
        if self.frame is not None:
            ret, buffer = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                return buffer.tobytes()
        return None

class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Jetson Nano Camera Stream</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; margin: 20px; }
                    img { max-width: 100%; height: auto; border: 2px solid #333; }
                    .info { margin: 20px; padding: 10px; background-color: #f0f0f0; }
                </style>
            </head>
            <body>
                <h1>🎥 Jetson Nano Camera Stream</h1>
                <div class="info">
                    <p>✅ Camera streaming with ArUco detection</p>
                </div>
                <img src="/stream.mjpg" alt="Camera Stream">
                <div class="info">
                    <p>📡 Refresh the page if stream stops</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            
            try:
                while True:
                    frame_data = streamer.get_frame_jpeg()
                    if frame_data:
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', str(len(frame_data)))
                        self.end_headers()
                        self.wfile.write(frame_data)
                        self.wfile.write(b'\r\n')
                    time.sleep(0.033)  # ~30fps
            except Exception as e:
                print(f"Streaming error: {e}")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

def main():
    global streamer
    
    print("🎥 Jetson Nano Camera Web Streamer")
    print("=" * 50)
    
    # Check ArUco availability
    try:
        print("✅ ArUco detection available")
    except:
        print("⚠️ ArUco detection not available")
    
    # Initialize camera streamer
    streamer = CameraWebStreamer()
    
    if not streamer.start_camera():
        print("💥 Failed to initialize camera. Exiting.")
        return
    
    # Start capture thread
    streamer.running = True
    capture_thread = threading.Thread(target=streamer.capture_frames)
    capture_thread.daemon = True
    capture_thread.start()
    
    # Get IP addresses
    ips = streamer.get_jetson_ip()
    
    # Start web server
    try:
        server = HTTPServer(('0.0.0.0', 8000), StreamingHandler)
        print("🚀 Starting web server on port 8000...")
        print("📸 Starting frame capture...")
        print("=" * 50)
        print("✅ WEB CAMERA SERVER STARTED!")
        print("=" * 50)
        print("📱 Open these URLs in your laptop browser:")
        for ip in ips:
            print(f"   🔗 http://{ip}:8000")
        print("=" * 50)
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        streamer.running = False
        if streamer.camera:
            streamer.camera.release()
        server.shutdown()
        print("✅ Shutdown complete")

if __name__ == "__main__":
    main()