#!/usr/bin/env python3
"""
Simple CSI Camera Test
Just capture one frame from CSI camera and save it
For OpenCV 3.2.0 on Jetson Nano
"""

import cv2

def capture_single_frame():
    """Capture one frame from CSI camera"""
    
    print("📷 Starting CSI camera...")
    
    # Try multiple approaches for OpenCV 3.2.0
    
    # Method 1: Try V4L2 first (simpler)
    print("🔍 Trying V4L2 method...")
    cap = cv2.VideoCapture(0)  # /dev/video0
    
    if cap.isOpened():
        print("✅ V4L2 camera opened")
        ret, frame = cap.read()
        if ret:
            print(f"✅ V4L2 frame captured: {frame.shape}")
            cv2.imwrite('csi_frame_v4l2.jpg', frame)
            print("💾 Saved as csi_frame_v4l2.jpg")
            cap.release()
            return True
        else:
            print("❌ V4L2 opened but no frame")
            cap.release()
    else:
        print("❌ V4L2 failed to open")
    
    # Method 2: Try GStreamer with minimal pipeline
    print("🔍 Trying minimal GStreamer...")
    pipeline = "nvarguscamerasrc ! nvvidconv ! videoconvert ! appsink"
    cap = cv2.VideoCapture(pipeline)
    
    if cap.isOpened():
        print("✅ GStreamer camera opened")
        ret, frame = cap.read()
        if ret:
            print(f"✅ GStreamer frame captured: {frame.shape}")
            cv2.imwrite('csi_frame_gstreamer.jpg', frame)
            print("💾 Saved as csi_frame_gstreamer.jpg")
            cap.release()
            return True
        else:
            print("❌ GStreamer opened but no frame")
            cap.release()
    else:
        print("❌ GStreamer failed to open")
    
    print("💥 Both methods failed")
    return False

if __name__ == "__main__":
    print("🎥 Simple CSI Camera Test")
    print("=" * 30)
    
    success = capture_single_frame()
    
    if success:
        print("🎉 SUCCESS! Check csi_frame.jpg")
    else:
        print("💥 FAILED! Camera not working")
        print("\n💡 Try:")
        print("1. Check camera connection")
        print("2. Run: gst-launch-1.0 nvarguscamerasrc ! fakesink")
        print("3. Restart: sudo systemctl restart nvargus-daemon")