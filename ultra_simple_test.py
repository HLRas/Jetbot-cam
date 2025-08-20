#!/usr/bin/env python3
"""
Ultra Simple Camera Test
Minimal pipeline to isolate the issue
"""

import cv2

def test_ultra_simple():
    """Test with absolute minimal pipeline"""
    
    # Bare minimum pipeline
    pipeline = "nvarguscamerasrc ! nvvidconv ! videoconvert ! appsink"
    
    print("📹 Ultra simple test...")
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    
    if cap.isOpened():
        print("✅ Camera opened")
        ret, frame = cap.read()
        if ret:
            print(f"✅ Frame: {frame.shape}")
            cv2.imwrite('ultra_simple.jpg', frame)
            print("💾 Saved ultra_simple.jpg")
        else:
            print("❌ No frame")
        cap.release()
        return ret
    else:
        print("❌ Failed to open")
        return False

if __name__ == "__main__":
    test_ultra_simple()
