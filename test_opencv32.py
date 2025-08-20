#!/usr/bin/env python3
"""
OpenCV 3.2.0 Compatible Camera Test
Works with older OpenCV syntax
"""

import cv2

def test_opencv32_camera():
    """Test camera with OpenCV 3.2.0 syntax"""
    print("🔍 Testing OpenCV 3.2.0 camera access...")
    print(f"OpenCV Version: {cv2.__version__}")
    
    # Test different approaches for OpenCV 3.2.0
    tests = [
        {
            "name": "GStreamer Pipeline",
            "source": "nvarguscamerasrc ! nvvidconv ! videoconvert ! appsink"
        },
        {
            "name": "Simple GStreamer", 
            "source": "nvarguscamerasrc ! appsink"
        },
        {
            "name": "V4L2 Device",
            "source": 0  # /dev/video0
        },
        {
            "name": "V4L2 Path",
            "source": "/dev/video0"
        }
    ]
    
    for test in tests:
        print(f"\n📹 Testing: {test['name']}")
        try:
            # OpenCV 3.2.0 uses single argument
            cap = cv2.VideoCapture(test['source'])
            
            if cap.isOpened():
                print("✅ Camera opened")
                
                # Try to capture frame
                ret, frame = cap.read()
                if ret:
                    print(f"✅ Frame captured: {frame.shape}")
                    cv2.imwrite(f"test_{test['name'].replace(' ', '_').lower()}.jpg", frame)
                    print(f"💾 Saved test frame")
                    cap.release()
                    return True
                else:
                    print("❌ No frame captured")
                    
                cap.release()
            else:
                print("❌ Failed to open camera")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_working_gstreamer():
    """Test with known working GStreamer pipeline"""
    print("\n🧪 Testing working GStreamer pipeline...")
    
    # This is the pipeline that works in command line
    pipeline = (
        "nvarguscamerasrc sensor-id=0 ! "
        "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=60/1 ! "
        "nvvidconv ! videoconvert ! appsink"
    )
    
    try:
        cap = cv2.VideoCapture(pipeline)
        if cap.isOpened():
            print("✅ Working pipeline opened")
            ret, frame = cap.read()
            if ret:
                print(f"✅ Working pipeline frame: {frame.shape}")
                cv2.imwrite("working_pipeline.jpg", frame)
                print("💾 Saved working_pipeline.jpg")
                cap.release()
                return True
            else:
                print("❌ Working pipeline no frame")
        else:
            print("❌ Working pipeline failed to open")
        cap.release()
    except Exception as e:
        print(f"❌ Working pipeline error: {e}")
    
    return False

def main():
    print("🎥 OpenCV 3.2.0 Camera Test")
    print("=" * 40)
    
    if test_opencv32_camera():
        print("\n🎉 SUCCESS! Found working camera method")
    elif test_working_gstreamer():
        print("\n🎉 SUCCESS! Working GStreamer pipeline found")
    else:
        print("\n💥 All tests failed")
        print("\n💡 Try these manual tests:")
        print("1. v4l2-ctl --device=/dev/video0 --stream-mmap")
        print("2. gst-launch-1.0 nvarguscamerasrc ! autovideosink")
        print("3. Check camera connection")

if __name__ == "__main__":
    main()
