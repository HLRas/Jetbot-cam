#!/usr/bin/env python3
"""
Headless ArUco Detection for Jetson Nano
Terminal output only - no GUI, no web streaming
"""

import cv2
import time
from image_processor import ImageProcessor

class HeadlessCamera:
    def __init__(self):
        self.camera = None
        self.running = False
        self.frame_count = 0
        self.image_processor = ImageProcessor(headless=True)  # Enable headless mode without tcp stuff
        
    def start_camera(self):
        """Initialize CSI camera"""
        print("🎥 Initializing CSI camera for headless operation...")
        
        pipeline = (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=10/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! appsink drop=1"
        )
        
        try:
            self.camera = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            
            if self.camera.isOpened():
                ret, test_frame = self.camera.read()
                if ret:
                    print(f"✅ Camera initialized successfully")
                    print(f"📹 Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                    return True
                else:
                    print("❌ Camera opened but cannot capture frames")
                    return False
            else:
                print("❌ Failed to open camera")
                return False
                
        except Exception as e:
            print(f"❌ Camera error: {e}")
            return False
            
    def run_detection(self, duration=None):
        """Run ArUco detection in headless mode"""
        if not self.start_camera():
            return
            
        print("🔍 Starting headless ArUco detection...")
        print("📊 Output: Terminal only")
        print("🛑 Press Ctrl+C to stop")
        print("-" * 50)
        
        self.running = True
        start_time = time.time()
        
        try:
            while self.running:
                ret, frame = self.camera.read()
                if ret:
                    self.frame_count += 1
                    
                    # Process frame for ArUco detection
                    self.image_processor.update_frame(frame)
                    
                    # Print frame info periodically
                    if self.frame_count % 100 == 0:
                        elapsed = time.time() - start_time
                        fps = self.frame_count / elapsed
                        print(f"📈 Frame {self.frame_count}, FPS: {fps:.1f}")
                    
                    # Check duration limit
                    if duration and (time.time() - start_time) > duration:
                        print(f"⏰ Duration limit reached: {duration}s")
                        break
                        
                else:
                    print(f"⚠️ Frame capture failed at frame {self.frame_count}")
                    time.sleep(0.1)
                    
                time.sleep(0.1)  # 10fps for headless mode
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping detection...")
        finally:
            self.stop()
            
    def stop(self):
        """Clean shutdown"""
        self.running = False
        if self.camera:
            self.camera.release()
        print("✅ Headless camera stopped")

def main():
    print("🚀 Headless ArUco Detection System")
    print("=" * 40)
    
    headless_cam = HeadlessCamera()
    
    # Run indefinitely (until Ctrl+C)
    headless_cam.run_detection()
    
    # Or run for specific duration:
    # headless_cam.run_detection(duration=60)  # Run for 60 seconds

if __name__ == '__main__':
    main()
