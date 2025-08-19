#!/usr/bin/env python3
"""
Simple camera test script to find working pipeline
"""

import cv2

def test_pipeline(name, pipeline, use_gstreamer=True):
    print(f"\n🔍 Testing: {name}")
    print(f"Pipeline: {pipeline}")
    
    try:
        if use_gstreamer:
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        else:
            cap = cv2.VideoCapture(pipeline, cv2.CAP_V4L2)
        
        print(f"Camera opened: {cap.isOpened()}")
        
        if cap.isOpened():
            ret, frame = cap.read()
            print(f"Frame captured: {ret}")
            if ret:
                print(f"✅ SUCCESS! Frame shape: {frame.shape}")
                cap.release()
                return True
            else:
                print("❌ Failed to capture frame")
        else:
            print("❌ Failed to open camera")
        
        cap.release()
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎥 Testing different camera pipelines...")
    
    # Test pipelines that match gst-launch syntax more closely
    pipelines = [
        # Simple pipeline matching your working gst-launch
        {
            "name": "Simple nvarguscamerasrc",
            "pipeline": "nvarguscamerasrc ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink",
            "gstreamer": True
        },
        # Without memory specification
        {
            "name": "No NVMM memory",
            "pipeline": "nvarguscamerasrc ! video/x-raw, width=1280, height=720, format=NV12, framerate=10/1 ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink",
            "gstreamer": True
        },
        # Basic pipeline
        {
            "name": "Very basic",
            "pipeline": "nvarguscamerasrc ! nvvidconv ! videoconvert ! appsink",
            "gstreamer": True
        },
        # With sensor ID
        {
            "name": "With sensor-id=0",
            "pipeline": "nvarguscamerasrc sensor-id=0 ! nvvidconv ! videoconvert ! appsink",
            "gstreamer": True
        },
        # V4L2 alternatives
        {
            "name": "V4L2 /dev/video0",
            "pipeline": "/dev/video0",
            "gstreamer": False
        },
        {
            "name": "V4L2 device 0",
            "pipeline": 0,
            "gstreamer": False
        }
    ]
    
    working_pipeline = None
    
    for test in pipelines:
        if test_pipeline(test["name"], test["pipeline"], test["gstreamer"]):
            working_pipeline = test
            break
    
    if working_pipeline:
        print(f"\n🎉 FOUND WORKING PIPELINE: {working_pipeline['name']}")
        print(f"Pipeline: {working_pipeline['pipeline']}")
        print(f"Use GStreamer: {working_pipeline['gstreamer']}")
    else:
        print("\n❌ No working pipeline found")
        print("\nAdditional debugging steps:")
        print("1. Check OpenCV GStreamer support:")
        print("   python -c \"import cv2; print(cv2.getBuildInformation())\" | grep -i gstreamer")
        print("2. Check available cameras:")
        print("   ls -la /dev/video*")
        print("3. Check permissions:")
        print("   groups $USER")

if __name__ == "__main__":
    main()
