#!/usr/bin/env python3
"""
Quick Camera Test - Fix Green Screen Issue
"""

import cv2
import time

def test_camera_formats():
    """Test different camera formats to fix green screen"""
    print("🔧 Testing camera formats to fix green screen...")
    
    # Test different V4L2 formats
    formats_to_try = [
        {"name": "YUYV", "fourcc": cv2.VideoWriter_fourcc('Y','U','Y','V')},
        {"name": "MJPG", "fourcc": cv2.VideoWriter_fourcc('M','J','P','G')},
        {"name": "BGR3", "fourcc": cv2.VideoWriter_fourcc('B','G','R','3')},
        {"name": "RGB3", "fourcc": cv2.VideoWriter_fourcc('R','G','B','3')},
    ]
    
    for fmt in formats_to_try:
        print(f"\n🧪 Testing {fmt['name']} format...")
        
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        
        if cap.isOpened():
            # Set format
            cap.set(cv2.CAP_PROP_FOURCC, fmt['fourcc'])
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Get actual format
            actual_fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            actual_format = "".join([chr((actual_fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            print(f"   📝 Requested: {fmt['name']}, Got: {actual_format}")
            
            # Test frame capture
            for i in range(5):  # Try a few frames
                ret, frame = cap.read()
                if ret:
                    # Check if frame looks valid (not all green)
                    mean_color = frame.mean(axis=(0,1))
                    print(f"   Frame {i+1}: BGR mean = {mean_color}")
                    
                    # If green channel is way higher than red/blue, it's the green screen issue
                    if mean_color[1] > mean_color[0] + 50 and mean_color[1] > mean_color[2] + 50:
                        print(f"   ❌ Green screen detected with {fmt['name']}")
                    else:
                        print(f"   ✅ Normal colors with {fmt['name']}!")
                        
                        # Save a test frame
                        cv2.imwrite(f'test_frame_{fmt["name"]}.jpg', frame)
                        print(f"   💾 Saved test frame as test_frame_{fmt['name']}.jpg")
                        cap.release()
                        return fmt
                        
                time.sleep(0.1)  # Small delay between frames
                
        cap.release()
    
    print("\n🔍 Trying CSI camera with different color conversions...")
    
    # Try CSI camera with different color space conversions
    csi_tests = [
        {
            "name": "CSI with YUV conversion",
            "pipeline": (
                "nvarguscamerasrc sensor-id=0 ! "
                "video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! "
                "nvvidconv flip-method=0 ! "
                "video/x-raw, format=I420 ! "
                "videoconvert ! "
                "video/x-raw, format=BGR ! appsink"
            )
        },
        {
            "name": "CSI with RGB conversion", 
            "pipeline": (
                "nvarguscamerasrc sensor-id=0 ! "
                "video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! "
                "nvvidconv flip-method=0 ! "
                "video/x-raw, format=RGB ! "
                "videoconvert ! "
                "video/x-raw, format=BGR ! appsink"
            )
        }
    ]
    
    for test in csi_tests:
        print(f"\n🧪 Testing {test['name']}...")
        
        cap = cv2.VideoCapture(test['pipeline'], cv2.CAP_GSTREAMER)
        
        if cap.isOpened():
            for i in range(3):
                ret, frame = cap.read()
                if ret:
                    mean_color = frame.mean(axis=(0,1))
                    print(f"   Frame {i+1}: BGR mean = {mean_color}")
                    
                    if not (mean_color[1] > mean_color[0] + 50 and mean_color[1] > mean_color[2] + 50):
                        print(f"   ✅ Normal colors with {test['name']}!")
                        cv2.imwrite(f'test_frame_csi_{i}.jpg', frame)
                        cap.release()
                        return test
                        
                time.sleep(0.2)
                
        cap.release()
    
    return None

def main():
    print("🎥 Camera Green Screen Fix Test")
    print("=" * 50)
    
    working_format = test_camera_formats()
    
    if working_format:
        print(f"\n🎉 Found working format: {working_format['name']}")
        print("✅ You can now update your ssh_cam.py script with this format!")
    else:
        print("\n❌ Could not find a working format")
        print("💡 Try these manual troubleshooting steps:")
        print("   1. Check camera connection")
        print("   2. Run: v4l2-ctl --list-devices")
        print("   3. Run: v4l2-ctl --list-formats-ext")
        print("   4. Try different CSI port if available")

if __name__ == "__main__":
    main()
