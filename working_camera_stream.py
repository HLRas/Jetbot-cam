#!/usr/bin/env python3
"""
Jetson Nano Camera Stream with ArUco Detection
Using System OpenCV 3.2.0 (WORKING VERSION)
"""

import cv2
import threading
import time
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess

class CameraStreamer:
    def __init__(self):
        self.frame = None
        self.camera = None
        self.running = False
        self.frame_count = 0
        
        # ArUco setup for OpenCV 3.2.0
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        self.aruco_params = cv2.aruco.DetectorParameters_create()
        
    def get_ip_addresses(self):
        """Get Jetson IP addresses"""
        try:
            result = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE, text=True)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                return [ip for ip in ips if ip and not ip.startswith('127.')]
        except:
            pass
        return ['localhost']
    
    def start_camera(self):
        """Start CSI camera with OpenCV 3.2.0"""
        print("🎥 Starting CSI camera with OpenCV 3.2.0...")
        
        # Working pipeline for OpenCV 3.2.0
        pipeline = (
            "nvarguscamerasrc sensor-id=0 ! "
            "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=60/1 ! "
            "nvvidconv ! videoconvert ! appsink"
        )
        
        try:
            self.camera = cv2.VideoCapture(pipeline)
            
            if self.camera.isOpened():
                # Test frame capture
                ret, test_frame = self.camera.read()
                if ret:
                    print(f"✅ Camera working! Resolution: {test_frame.shape}")
                    return True
                else:
                    print("❌ Camera opened but no frames")
            else:
                print("❌ Camera failed to open")
                
        except Exception as e:
            print(f"❌ Camera error: {e}")
            
        return False
    
    def process_aruco(self, frame):
        """Detect and draw ArUco markers"""
        # Convert to grayscale for ArUco detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect ArUco markers
        corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)
        
        # Draw detected markers
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            # Add marker info text
            for i, marker_id in enumerate(ids.flatten()):
                cv2.putText(frame, f"ArUco ID: {marker_id}", 
                           (10, 120 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        return frame
    
    def capture_frames(self):
        """Continuous frame capture and processing"""
        print("📸 Starting frame capture...")
        
        while self.running and self.camera:
            ret, frame = self.camera.read()
            
            if ret:
                self.frame_count += 1
                
                # Add overlay info
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, "Jetson Nano CSI Camera", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, timestamp, 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(frame, f"Frame: {self.frame_count}", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Process ArUco markers
                frame = self.process_aruco(frame)
                
                # Store processed frame
                self.frame = frame.copy()
                
                # Status update
                if self.frame_count % 100 == 0:
                    print(f"📊 Processed {self.frame_count} frames")
            else:
                print("⚠️ Frame capture failed")
                time.sleep(0.1)
    
    def get_frame_jpeg(self):
        """Get current frame as JPEG"""
        if self.frame is not None:
            ret, buffer = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                return buffer.tobytes()
        return None
    
    def stop(self):
        """Stop camera and cleanup"""
        self.running = False
        if self.camera:
            self.camera.release()

class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Jetson Nano ArUco Camera</title>
                <style>
                    body { font-family: Arial; text-align: center; margin: 20px; }
                    img { max-width: 100%; border: 2px solid #333; }
                    .info { margin: 20px; padding: 10px; background: #f0f0f0; }
                </style>
            </head>
            <body>
                <h1>🎥 Jetson Nano CSI Camera with ArUco Detection</h1>
                <div class="info">
                    <p>✅ OpenCV 3.2.0 | ✅ CSI Camera | ✅ ArUco Detection</p>
                </div>
                <img src="/stream.mjpg" alt="Camera Stream">
                <div class="info">
                    <p>🔄 Refresh page if stream stops</p>
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
                    frame_data = camera_streamer.get_frame_jpeg()
                    if frame_data:
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', str(len(frame_data)))
                        self.end_headers()
                        self.wfile.write(frame_data)
                        self.wfile.write(b'\r\n')
                    time.sleep(0.033)  # ~30fps
            except:
                pass
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def main():
    global camera_streamer
    
    print("🎥 Jetson Nano ArUco Camera Stream")
    print("=" * 50)
    print("Using System OpenCV 3.2.0 (Hardware Compatible)")
    print("=" * 50)
    
    # Initialize camera
    camera_streamer = CameraStreamer()
    
    if not camera_streamer.start_camera():
        print("💥 Camera initialization failed!")
        return
    
    # Start capture thread
    camera_streamer.running = True
    capture_thread = threading.Thread(target=camera_streamer.capture_frames)
    capture_thread.daemon = True
    capture_thread.start()
    
    # Get IP addresses
    ips = camera_streamer.get_ip_addresses()
    
    # Start web server
    try:
        server = HTTPServer(('0.0.0.0', 8000), StreamHandler)
        
        print("🚀 Web server starting...")
        print("=" * 50)
        print("✅ CAMERA STREAM ACTIVE!")
        print("=" * 50)
        print("📱 View in browser:")
        for ip in ips:
            print(f"   🔗 http://{ip}:8000")
        print("=" * 50)
        print("Press Ctrl+C to stop")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        camera_streamer.stop()
        server.shutdown()
        print("✅ Stopped successfully")

if __name__ == "__main__":
    main()
