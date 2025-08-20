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
            self.aruco_available = hasattr(cv2, 'aruco')
            if self.aruco_available:
                print("✅ ArUco detection available")
            else:
                print("⚠️ ArUco detection not available - skipping marker detection")
        except Exception as e:
            print(f"⚠️ ArUco detection error: {e}")
            self.aruco_available = False
        
    def update_frame(self, new_frame: Optional[np.ndarray]) -> None:
        """Update the current frame and maintain history"""
        if new_frame is not None:
            # Store previous frame in history
            if self.current_frame is not None:
                self.frames.append(self.current_frame.copy())
                if len(self.frames) > self.num_frames:
                    self.frames.pop(0)  # Remove oldest frame
            
            # Store new frame as current
            self.current_frame = new_frame.copy()
            
            self.aruco_detection()
        else:
            print("⚠️ Received None frame, not updating")
    
    def aruco_detection(self):
        """Detect ArUco markers in background (no display)"""
        if self.current_frame is None or not self.aruco_available:
            return
        
        try:
            # Load the image
            image = self.get_current_frame()

            # Convert the image to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Create ArUco dictionary and parameters (OpenCV 4.5.1)
            aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
            parameters = cv2.aruco.DetectorParameters_create()

            # Detect the markers
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
            
            # Print the detected markers
            if ids is not None and len(ids) > 0:
                print(f"Detected markers: {ids.flatten()}")
            else:
                print("No markers detected")
                
        except Exception as e:
            print(f"ArUco detection error: {e}")
            # Don't disable ArUco on detection errors, only on init errors
    
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
