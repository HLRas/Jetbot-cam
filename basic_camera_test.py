#!/usr/bin/env python3
"""
Minimal GStreamer CSI Camera Test
Just capture one frame and save it
"""

import cv2

def test_basic_csi():
    """Test basic CSI camera - capture one frame"""
    
    # Simple working pipeline from your successful GStreamer test
    pipeline = (
        "nvarguscamerasrc sensor-id=0 ! "
        "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=60/1 ! "
        "nvvidconv ! "
        "video/x-raw, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! "
        "appsink"
    )
    
    print("📹 Opening CSI camera...")
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    
    if not cap.isOpened():
        print("❌ Failed to open camera")
        return False
    
    print("✅ Camera opened")
    print("📸 Capturing frame...")
    
    ret, frame = cap.read()
    
    if ret:
        print(f"✅ Frame captured: {frame.shape[1]}x{frame.shape[0]}")
        cv2.imwrite('csi_test.jpg', frame)
        print("💾 Saved as csi_test.jpg")
        result = True
    else:
        print("❌ Failed to capture frame")
        result = False
    
    cap.release()
    return result

if __name__ == "__main__":
    print("🎥 Basic CSI Camera Test")
    print("=" * 30)
    
    if test_basic_csi():
        print("🎉 SUCCESS! Camera is working")
    else:
        print("💥 FAILED! Camera not working")
