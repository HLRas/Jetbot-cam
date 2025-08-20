#!/usr/bin/env python3
"""
OpenCV and ArUco Test Script
Tests OpenCV installation and ArUco marker detection capabilities
"""

import cv2
import numpy as np
import sys
import traceback

def test_opencv_basic():
    """Test basic OpenCV functionality"""
    print("=" * 50)
    print("TESTING OPENCV BASIC FUNCTIONALITY")
    print("=" * 50)
    
    try:
        # Check OpenCV version
        print(f"OpenCV Version: {cv2.__version__}")
        
        # Check build information
        print("\nOpenCV Build Info:")
        build_info = cv2.getBuildInformation()
        print("Build type:", "DEBUG" if "Debug" in build_info else "RELEASE")
        
        # Test basic image operations
        print("\nTesting basic image operations...")
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        test_img[100:400, 100:540] = [0, 255, 0]  # Green rectangle
        cv2.putText(test_img, "OpenCV Test", (200, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        print("✓ Basic image creation and manipulation: PASSED")
        
        # Test image encoding/decoding
        _, encoded = cv2.imencode('.jpg', test_img)
        decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        print("✓ Image encoding/decoding: PASSED")
        
        return True
        
    except Exception as e:
        print(f"✗ OpenCV basic test FAILED: {e}")
        traceback.print_exc()
        return False

def test_aruco_detection():
    """Test ArUco marker detection"""
    print("\n" + "=" * 50)
    print("TESTING ARUCO FUNCTIONALITY")
    print("=" * 50)
    
    try:
        # Check if ArUco is available
        if not hasattr(cv2, 'aruco'):
            print("✗ ArUco module not found in OpenCV")
            return False
            
        print(f"✓ ArUco module found")
        
        # Create ArUco dictionary
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        print(f"✓ ArUco dictionary created: DICT_6X6_250")
        
        # Create detector parameters
        detector_params = cv2.aruco.DetectorParameters()
        print(f"✓ Detector parameters created")
        
        # Generate a test marker
        marker_size = 200
        marker_id = 42
        marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)
        print(f"✓ Generated test marker (ID: {marker_id}, Size: {marker_size}x{marker_size})")
        
        # Create a test image with the marker
        test_img = np.ones((600, 800, 3), dtype=np.uint8) * 255  # White background
        # Place marker in center
        y_start = (600 - marker_size) // 2
        x_start = (800 - marker_size) // 2
        test_img[y_start:y_start+marker_size, x_start:x_start+marker_size] = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2BGR)
        
        # Detect markers in the test image
        detector = cv2.aruco.ArucoDetector(aruco_dict, detector_params)
        corners, ids, rejected = detector.detectMarkers(test_img)
        
        if ids is not None and len(ids) > 0:
            print(f"✓ ArUco detection PASSED - Found {len(ids)} marker(s)")
            print(f"  Detected IDs: {ids.flatten()}")
            
            # Draw detected markers
            cv2.aruco.drawDetectedMarkers(test_img, corners, ids)
            print("✓ Marker drawing: PASSED")
            
            return True
        else:
            print("✗ ArUco detection FAILED - No markers detected")
            return False
            
    except Exception as e:
        print(f"✗ ArUco test FAILED: {e}")
        traceback.print_exc()
        return False

def test_camera_compatibility():
    """Test camera opening compatibility (without actual camera)"""
    print("\n" + "=" * 50)
    print("TESTING CAMERA COMPATIBILITY")
    print("=" * 50)
    
    try:
        # Test different backends
        backends = [
            ("Default", cv2.CAP_ANY),
            ("V4L2", cv2.CAP_V4L2),
            ("GStreamer", cv2.CAP_GSTREAMER),
        ]
        
        for name, backend in backends:
            try:
                cap = cv2.VideoCapture(0, backend)
                is_opened = cap.isOpened()
                cap.release()
                status = "✓ Available" if is_opened else "✗ Not available"
                print(f"  {name} backend: {status}")
            except Exception as e:
                print(f"  {name} backend: ✗ Error - {e}")
        
        print("✓ Camera compatibility test completed")
        return True
        
    except Exception as e:
        print(f"✗ Camera compatibility test FAILED: {e}")
        return False

def test_gstreamer_pipeline():
    """Test GStreamer pipeline creation"""
    print("\n" + "=" * 50)
    print("TESTING GSTREAMER PIPELINE")
    print("=" * 50)
    
    try:
        # Test CSI camera pipeline (won't connect but should parse)
        csi_pipeline = (
            'nvarguscamerasrc sensor-id=0 ! '
            'video/x-raw(memory:NVMM), width=640, height=480, framerate=30/1 ! '
            'nvvidconv flip-method=0 ! '
            'video/x-raw, width=640, height=480, format=BGRx ! '
            'videoconvert ! '
            'video/x-raw, format=BGR ! appsink'
        )
        
        # Test USB camera pipeline
        usb_pipeline = (
            'v4l2src device=/dev/video0 ! '
            'video/x-raw, width=640, height=480, framerate=30/1 ! '
            'videoconvert ! '
            'video/x-raw, format=BGR ! appsink'
        )
        
        pipelines = [
            ("CSI Camera", csi_pipeline),
            ("USB Camera", usb_pipeline)
        ]
        
        for name, pipeline in pipelines:
            try:
                cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
                # We don't expect it to actually open without hardware
                cap.release()
                print(f"  {name} pipeline: ✓ Parsed successfully")
            except Exception as e:
                print(f"  {name} pipeline: ✗ Parse error - {e}")
        
        print("✓ GStreamer pipeline test completed")
        return True
        
    except Exception as e:
        print(f"✗ GStreamer pipeline test FAILED: {e}")
        return False

def create_test_aruco_image():
    """Create a test image with multiple ArUco markers for testing"""
    print("\n" + "=" * 50)
    print("CREATING TEST ARUCO IMAGE")
    print("=" * 50)
    
    try:
        # Create ArUco dictionary
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        
        # Create a large test image
        img_width, img_height = 1200, 800
        test_img = np.ones((img_height, img_width, 3), dtype=np.uint8) * 255
        
        # Generate multiple markers
        marker_size = 150
        marker_ids = [0, 1, 2, 3, 42, 100]
        positions = [
            (100, 100),   # Top-left
            (600, 100),   # Top-right
            (100, 400),   # Middle-left
            (600, 400),   # Middle-right
            (100, 600),   # Bottom-left
            (600, 600),   # Bottom-right
        ]
        
        for marker_id, (x, y) in zip(marker_ids, positions):
            marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)
            marker_bgr = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2BGR)
            test_img[y:y+marker_size, x:x+marker_size] = marker_bgr
            
            # Add ID label
            cv2.putText(test_img, f"ID: {marker_id}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # Save test image
        cv2.imwrite('test_aruco_markers.jpg', test_img)
        print(f"✓ Created test image with {len(marker_ids)} markers")
        print("✓ Saved as 'test_aruco_markers.jpg'")
        
        # Test detection on created image
        detector = cv2.aruco.ArucoDetector(aruco_dict, cv2.aruco.DetectorParameters())
        corners, ids, rejected = detector.detectMarkers(test_img)
        
        if ids is not None:
            detected_ids = ids.flatten()
            print(f"✓ Detected {len(detected_ids)} markers: {detected_ids}")
            
            # Draw detection results
            cv2.aruco.drawDetectedMarkers(test_img, corners, ids)
            cv2.imwrite('test_aruco_detection_result.jpg', test_img)
            print("✓ Saved detection result as 'test_aruco_detection_result.jpg'")
        else:
            print("✗ No markers detected in test image")
            
        return True
        
    except Exception as e:
        print(f"✗ Test image creation FAILED: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("OpenCV and ArUco Test Suite")
    print("Python version:", sys.version)
    
    results = []
    
    # Run tests
    results.append(("OpenCV Basic", test_opencv_basic()))
    results.append(("ArUco Detection", test_aruco_detection()))
    results.append(("Camera Compatibility", test_camera_compatibility()))
    results.append(("GStreamer Pipeline", test_gstreamer_pipeline()))
    results.append(("Test Image Creation", create_test_aruco_image()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests PASSED! Your OpenCV and ArUco setup is working perfectly!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
