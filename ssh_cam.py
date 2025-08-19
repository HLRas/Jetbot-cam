#!/usr/bin/env python3
"""
Simple Web Camera Stream for Jetson Nano
No X11 required - view in any web browser
"""

import cv2
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import os
from typing import List, Optional, Any
import numpy as np
from image_processor import ImageProcessor

class CameraWebStreamer:
    def __init__(self):
        self.frame = None
        self.camera = None
        self.running = False
        self.frame_count = 0
        self.image_processor = ImageProcessor()  # Instantiate ImageProcessor
        
    def get_jetson_ip(self) -> List[str]:
        """Get Jetson IP addresses"""
        try:
            # Try multiple methods to get IP
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                return [ip for ip in ips if ip and not ip.startswith('127.')]
        except:
            pass
            
        try:
            # Fallback method
            result = subprocess.run(['ip', 'route', 'get', '1'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'src' in line:
                        ip = line.split('src')[1].split()[0]
                        return [ip]
        except:
            pass
            
        return ['localhost']
    
    def start_camera(self) -> bool:
        """Initialize camera with error handling"""
        print("🎥 Initializing camera...")
        
        # GStreamer pipeline for PiCamera Module v2
        gst_pipeline = (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=10/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! appsink drop=1"
        )
        
        self.camera = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        
        if not self.camera.isOpened():
            print("❌ Failed to open camera with GStreamer pipeline")
            print("🔧 Troubleshooting tips:")
            print("   - Check camera connection to CSI port")
            print("   - Run: ls /dev/video* to check camera devices")
            print("   - Try: dmesg | grep -i camera")
            return False
            
        # Test frame capture
        ret, test_frame = self.camera.read()
        if not ret:
            print("❌ Camera opened but cannot capture frames")
            return False
            
        print("✅ Camera initialized successfully")
        print(f"📹 Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
        return True
        
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
                           (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Store frame for streaming - use current frame directly
                self.frame = frame.copy()
                
                # Update ImageProcessor with the new frame (for ArUco detection)
                self.image_processor.update_frame(frame)
            else:
                print(f"⚠️ Frame capture failed at frame {self.frame_count}")
                time.sleep(0.1)
                
            time.sleep(0.033)  # ~30fps max
            
    def start_streaming(self, port: int = 8000) -> None:
        """Start the web streaming server"""
        ips = self.get_jetson_ip()
        
        print(f"🚀 Starting web server on port {port}...")
        
        # Start camera capture thread
        self.running = True
        capture_thread = threading.Thread(target=self.capture_frames)
        capture_thread.daemon = True
        capture_thread.start()
        
        # Create HTTP server
        server = HTTPServer(('', port), lambda *args: StreamHandler(self, *args))
        
        print("=" * 50)
        print("✅ WEB CAMERA SERVER STARTED!")
        print("=" * 50)
        print("📱 Open these URLs in your laptop browser:")
        for ip in ips:
            print(f"   🔗 http://{ip}:{port}")
        print("")
        print("💡 If you don't know the Jetson IP, try these commands:")
        print("   hostname -I")
        print("   ip addr show")
        print("")
        print("🛑 Press Ctrl+C to stop server")
        print("=" * 50)
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
        finally:
            self.stop()
            
    def get_image_processor(self) -> ImageProcessor:
        """Get the ImageProcessor instance for accessing stored frames"""
        return self.image_processor
            
    def stop(self) -> None:
        """Clean shutdown"""
        self.running = False
        if self.camera:
            self.camera.release()
        # Clear stored frames
        self.image_processor.clear_frames()
        print("✅ Camera stream stopped")

class StreamHandler(BaseHTTPRequestHandler):
    def __init__(self, streamer: CameraWebStreamer, *args: Any, **kwargs: Any) -> None:
        self.streamer = streamer
        super().__init__(*args, **kwargs)
        
    def do_GET(self) -> None:
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Jetson Nano Camera Stream</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .camera-feed {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            backdrop-filter: blur(10px);
        }}
        .stream-img {{
            max-width: 100%;
            max-height: 80vh;
            border-radius: 10px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        .controls {{
            margin: 20px 0;
        }}
        .btn {{
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 12px 24px;
            margin: 8px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
        }}
        .btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }}
        .status {{
            background: rgba(0,255,0,0.2);
            border-radius: 10px;
            padding: 10px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Jetson Nano Live Camera</h1>
        <div class="status">
            <p>📡 Streaming live from PiCamera Module v2</p>
            <p>📹 Resolution: 1280x720 @ ~10fps</p>
        </div>
        
        <div class="camera-feed">
            <img id="stream" class="stream-img" src="/stream.mjpg" alt="Camera Stream">
        </div>
        
        <div class="controls">
            <button class="btn" onclick="location.reload()">🔄 Refresh</button>
            <button class="btn" onclick="toggleFullscreen()">🖥️ Fullscreen</button>
            <button class="btn" onclick="saveFrame()">📸 Save Frame</button>
        </div>
        
        <p>💡 Tip: Right-click the image to save a snapshot</p>
    </div>
    
    <script>
        function toggleFullscreen() {{
            const img = document.getElementById('stream');
            if (document.fullscreenElement) {{
                document.exitFullscreen();
            }} else {{
                img.requestFullscreen();
            }}
        }}
        
        function saveFrame() {{
            const img = document.getElementById('stream');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            ctx.drawImage(img, 0, 0);
            
            const link = document.createElement('a');
            link.download = 'jetson_camera_' + new Date().getTime() + '.png';
            link.href = canvas.toDataURL();
            link.click();
        }}
        
        // Auto-refresh if stream stops
        document.getElementById('stream').onerror = function() {{
            setTimeout(() => {{ this.src = '/stream.mjpg?' + new Date().getTime(); }}, 2000);
        }};
    </script>
</body>
</html>'''
            self.wfile.write(html.encode())
            
        elif self.path.startswith('/stream.mjpg'):
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            
            try:
                while True:
                    if self.streamer.frame is not None:
                        # Encode frame as JPEG
                        ret, buffer = cv2.imencode('.jpg', self.streamer.frame, 
                                                 [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if ret:
                            self.wfile.write(b'--frame\r\n')
                            self.send_header('Content-Type', 'image/jpeg')
                            self.send_header('Content-Length', len(buffer))
                            self.end_headers()
                            self.wfile.write(buffer.tobytes())
                            self.wfile.write(b'\r\n')
                    time.sleep(0.033)  # ~30fps
            except Exception as e:
                print(f"Client disconnected: {e}")
                
    def log_message(self, format: str, *args: Any) -> None:
        # Suppress HTTP log messages
        return

def main() -> None:
    streamer = CameraWebStreamer()
    
    if not streamer.start_camera():
        print("❌ Failed to initialize camera")
        return
        
    try:
        streamer.start_streaming(port=8000)
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        streamer.stop()

if __name__ == '__main__':
    main()