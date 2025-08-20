#!/usr/bin/env python3
"""
Debug OpenCV Camera Access
Test different methods to isolate the issue
"""

import cv2
import subprocess

def test_opencv_backends():
    """Test OpenCV with different backends"""
    print("🔍 Testing OpenCV backends...")
    
    backends = [
        ("GStreamer", cv2.CAP_GSTREAMER),
        ("V4L2", cv2.CAP_V4L2),
        ("Any", cv2.CAP_ANY)
    ]
    
    for name, backend in backends:
        print(f"\n📹 Testing {name} backend...")
        try:
            cap = cv2.VideoCapture(0, backend)
            if cap.isOpened():
                print(f"✅ {name}: Camera opened")
                ret, frame = cap.read()
                if ret:
                    print(f"✅ {name}: Frame captured {frame.shape}")
                else:
                    print(f"❌ {name}: No frame")
                cap.release()
            else:
                print(f"❌ {name}: Failed to open")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")

def test_gstreamer_minimal():
    """Test minimal GStreamer pipelines"""
    print("\n🔍 Testing minimal GStreamer pipelines...")
    
    pipelines = [
        "nvarguscamerasrc ! appsink",
        "nvarguscamerasrc ! videoconvert ! appsink",
        "nvarguscamerasrc ! nvvidconv ! appsink",
        "v4l2src device=/dev/video0 ! appsink"
    ]
    
    for pipeline in pipelines:
        print(f"\n📹 Testing: {pipeline}")
        try:
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            if cap.isOpened():
                print("✅ Pipeline opened")
                cap.release()
            else:
                print("❌ Pipeline failed")
        except Exception as e:
            print(f"❌ Error: {e}")

def check_opencv_info():
    """Check OpenCV build information"""
    print("\n🔍 OpenCV Information:")
    print(f"OpenCV Version: {cv2.__version__}")
    
    build_info = cv2.getBuildInformation()
    
    # Check for key components
    components = ["GStreamer", "Video I/O", "V4L/V4L2"]
    for component in components:
        if component in build_info:
            print(f"✅ {component}: Available")
        else:
            print(f"❌ {component}: Missing")

def test_gst_command():
    """Test if gst-launch works from Python"""
    print("\n🔍 Testing gst-launch from Python...")
    
    cmd = [
        "gst-launch-1.0", "nvarguscamerasrc", "sensor-id=0", "num-buffers=1", "!",
        "nvvidconv", "!", "fakesink", "-v"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ gst-launch works from Python")
        else:
            print(f"❌ gst-launch failed: {result.stderr}")
    except Exception as e:
        print(f"❌ gst-launch error: {e}")

def main():
    print("🔧 OpenCV Camera Debug Script")
    print("=" * 50)
    
    check_opencv_info()
    test_opencv_backends()
    test_gstreamer_minimal()
    test_gst_command()
    
    print("\n" + "=" * 50)
    print("🏁 Debug complete!")

if __name__ == "__main__":
    main()
