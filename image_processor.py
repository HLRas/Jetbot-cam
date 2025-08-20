#!/usr/bin/env python3
"""
ImageProcessor class for handling frame storage and ArUco detection
Simplified version without grayscale display functionality
"""

from typing import List, Optional
import numpy as np
import cv2

class ImageProcessor:
    def __init__(self) -> None:
        """Initialize ImageProcessor with frame storage"""
        self.current_frame: Optional[np.ndarray] = None
        self.frames: List[np.ndarray] = []  # List to store recent frames
        self.num_frames = 2
        
        # Check if ArUco is available
        try:
            print("🔍 Checking ArUco availability...")
            self.aruco_available = hasattr(cv2, 'aruco')
            print(f"📊 cv2.aruco exists: {self.aruco_available}")
            
            if self.aruco_available:
                # Test if we can actually create ArUco objects
                test_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
                test_params = cv2.aruco.DetectorParameters()
                test_detector = cv2.aruco.ArucoDetector(test_dict, test_params)
                print("✅ ArUco detection available and tested")
            else:
                print("⚠️ ArUco detection not available - skipping marker detection")
        except Exception as e:
            print(f"⚠️ ArUco detection error during init: {e}")
            print(f"🔧 Error type: {type(e).__name__}")
            self.aruco_available = False
        
    def update_frame(self, new_frame: Optional[np.ndarray]) -> None:
        """Update the current frame and maintain history"""
        print(f"📥 update_frame called with frame: {new_frame.shape if new_frame is not None else 'None'}")
        
        if new_frame is not None:
            # Store previous frame in history
            if self.current_frame is not None:
                self.frames.append(self.current_frame.copy())
                if len(self.frames) > self.num_frames:
                    self.frames.pop(0)  # Remove oldest frame
            
            # Store new frame as current
            self.current_frame = new_frame.copy()
            print(f"✅ Frame stored, calling ArUco detection...")
            
            self.aruco_detection()
        else:
            print("⚠️ Received None frame, not updating")
    
    def aruco_detection(self):
        """Detect ArUco markers in background (no display)"""
        print("🔍 ArUco detection method called")
        
        if self.current_frame is None:
            print("⚠️ No current frame available for ArUco detection")
            return
        
        if not self.aruco_available:
            print("⚠️ ArUco not available, skipping detection")
            return
        
        print("✅ Entering ArUco detection try block")
        try:
            # Load the image
            image = self.get_current_frame()
            print(f"📸 Image shape: {image.shape if image is not None else 'None'}")

            # Convert the image to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            print(f"🔄 Converted to grayscale, shape: {gray.shape}")
            
            aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
            parameters = cv2.aruco.DetectorParameters()

            # Create the ArUco detector
            detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
            print("🎯 ArUco detector created")
            
            # Detect the markers
            corners, ids, rejected = detector.detectMarkers(gray)
            print(f"🔍 Detection completed - IDs: {ids}, Corners: {len(corners) if corners else 0}")
            
            # Print the detected markers
            if ids is not None and len(ids) > 0:
                print(f"✅ Detected markers: {ids.flatten()}")
            else:
                print("❌ No markers detected")
                
        except Exception as e:
            print(f"❌ ArUco detection error: {e}")
            print(f"🔧 Error type: {type(e).__name__}")
            # Silently disable ArUco if it causes issues
            self.aruco_available = False
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame"""
        return self.current_frame
    
    def get_previous_frames(self) -> List[np.ndarray]:
        """Get the list of previous frames"""
        return self.frames.copy()
    
    def get_frame_count(self) -> int:
        """Get the total number of frames processed"""
        return len(self.frames) + (1 if self.current_frame is not None else 0)
    
    def has_sufficient_frames(self, required_frames: int = 3) -> bool:
        """Check if we have enough frames for processing"""
        total_frames = len(self.frames) + (1 if self.current_frame is not None else 0)
        return total_frames >= required_frames
    
    def clear_frames(self) -> None:
        """Clear all stored frames"""
        self.current_frame = None
        self.frames.clear()
        print("🗑️ Cleared all stored frames")
