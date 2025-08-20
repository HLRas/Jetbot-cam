#!/usr/bin/env python3
"""
Simple CSI Camera Test - Working IMX219 Pipeline
"""

import cv2
import time

def test_working_pipeline():
    """Test CSI camera with known working pipeline"""
    
    # This is the exact pipeline that should work based on your diagnostic
    working_pipeline = (
        "nvarguscamerasrc sensor-id=0 ! "
        "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=60/1 ! "
        "nvvidconv flip-method=0 ! "
        "video/x-raw, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! appsink"
    )
    
    print("🧪 Testing working CSI pipeline...")
    print(f"Pipeline: {working_pipeline}")
    
    cap = cv2.VideoCapture(working_pipeline, cv2.CAP_GSTREAMER)
    
    if not cap.isOpened():
        print("❌ Failed to open camera with CSI pipeline")
        return False
    
    print("✅ Camera opened successfully!")
    
    # Try to capture frames
    for i in range(10):
        print(f"📸 Capturing frame {i+1}/10...")
        ret, frame = cap.read()
        
        if ret:
            print(f"✅ Frame {i+1}: {frame.shape[1]}x{frame.shape[0]} - Mean BGR: {frame.mean(axis=(0,1))}")
            
            # Save first frame
            if i == 0:
                cv2.imwrite('test_csi_frame.jpg', frame)
                print("💾 Saved test_csi_frame.jpg")
                
        else:
            print(f"❌ Failed to capture frame {i+1}")
            
        time.sleep(0.5)
    
    cap.release()
    return True

def test_v4l2_with_timeout():
    """Test V4L2 with timeout settings"""
    
    print("\n🧪 Testing V4L2 with timeout fix...")
    
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print("❌ Failed to open V4L2 camera")
        return False
    
    # Set buffer size and timeout
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 15)  # Lower FPS
    
    print("✅ V4L2 camera opened")
    
    # Give camera time to initialize
    print("⏳ Waiting for camera initialization...")
    time.sleep(2)
    
    # Try multiple times with longer timeout
    for i in range(5):
        print(f"📸 Attempting V4L2 capture {i+1}/5...")
        
        # Try to read with manual timeout handling
        start_time = time.time()
        ret, frame = cap.read()
        elapsed = time.time() - start_time
        
        print(f"   Read took {elapsed:.2f}s")
        
        if ret:
            print(f"✅ V4L2 Frame: {frame.shape[1]}x{frame.shape[0]}")
            cv2.imwrite(f'test_v4l2_frame_{i}.jpg', frame)
            cap.release()
            return True
        else:
            print(f"❌ V4L2 capture failed")
            time.sleep(1)
    
    cap.release()
    return False

def main():
    print("🎥 CSI Camera Working Pipeline Test")
    print("=" * 50)
    
    # Test 1: CSI with working pipeline
    if test_working_pipeline():
        print("\n🎉 CSI camera is working!")
    else:
        print("\n❌ CSI camera failed")
        
        # Test 2: V4L2 fallback
        if test_v4l2_with_timeout():
            print("🎉 V4L2 camera working as fallback!")
        else:
            print("❌ Both CSI and V4L2 failed")
            print("\n💡 Try these fixes:")
            print("   1. sudo systemctl restart nvargus-daemon")
            print("   2. Check camera connection")
            print("   3. Try: sudo modprobe tegra-camera")

if __name__ == "__main__":
    main()
