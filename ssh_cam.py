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
    
    # Simple CSI camera pipeline for OpenCV 3.2.0
    pipeline = (
        "nvarguscamerasrc sensor-id=0 ! "
        "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! "
        "nvvidconv ! videoconvert ! appsink"
    )
    
    # Open camera
    cap = cv2.VideoCapture(pipeline)
    
    if not cap.isOpened():
        print("❌ Failed to open CSI camera")
        return False
    
    print("✅ Camera opened successfully")
    
    # Capture one frame
    ret, frame = cap.read()
    
    if ret:
        print(f"✅ Frame captured: {frame.shape[1]}x{frame.shape[0]}")
        
        # Save the frame
        cv2.imwrite('csi_frame.jpg', frame)
        print("💾 Saved as csi_frame.jpg")
        
        result = True
    else:
        print("❌ Failed to capture frame")
        result = False
    
    # Clean up
    cap.release()
    
    return result

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