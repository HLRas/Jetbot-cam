#!/usr/bin/env python3
"""
ImageProcessor class for handling frame storage and ArUco detection
Simplified version without grayscale display functionality
"""

from typing import List, Optional
import numpy as np
import cv2

mtx = np.array([[1.31210204e+03, 0.00000000e+00, 6.23587581e+02],
 [0.00000000e+00, 1.32186888e+03, 3.29367318e+02],
 [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])

dist = np.array([ 0.13285292,  0.60199342, -0.01296075, -0.00628914, -3.23261949]) 

class ImageProcessor:
    def __init__(self, camera_mtx=None, camera_dist=None):
        """Initialize ImageProcessor with frame storage"""
        self.current_frame = None
        self.frames = []  # List to store recent frames
        self.num_frames = 2
        self.annotated_frame = None  # Frame with ArUco annotations

        # Set camera calibration parameters
        self.mtx = camera_mtx if camera_mtx is not None else mtx
        self.dist = camera_dist if camera_dist is not None else dist

        # Check if ArUco is available
        try:
            self.aruco_available = hasattr(cv2, 'aruco')
            if self.aruco_available:
                print("✅ ArUco detection available")

                # Create ArUco dictionary and parameters (OpenCV 4.5.1)
                self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
                self.parameters = cv2.aruco.DetectorParameters_create()
                self.parameters.adaptiveThreshWinSizeMin = 3
                self.parameters.adaptiveThreshWinSizeMax = 23
                self.parameters.adaptiveThreshWinSizeStep = 10
                self.parameters.adaptiveThreshConstant = 1
                self.parameters.polygonalApproxAccuracyRate = 0.03
                self.parameters.minMarkerPerimeterRate = 0.03
                self.parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
                self.parameters.cornerRefinementWinSize = 5
                self.parameters.cornerRefinementMaxIterations = 30
                self.parameters.cornerRefinementMinAccuracy = 0.1
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
            self.undistort_frame()
            self.aruco_detection()
        else:
            print("⚠️ Received None frame, not updating")
    
    def undistort_frame(self):
        """Undistort the current frame using camera calibration parameters"""
        if self.current_frame is not None:
            h, w = self.current_frame.shape[:2]
            new_mtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
            self.current_frame = cv2.undistort(self.current_frame, self.mtx, self.dist, None, new_mtx)
            # Crop the image to the valid region
            x, y, w, h = roi
            self.current_frame = self.current_frame[y:y+h, x:x+w]
        else:
            print("⚠️ No current frame to undistort")

    def aruco_detection(self):
        """Detect ArUco markers and create annotated frame for visualization"""
        if self.current_frame is None or not self.aruco_available:
            self.annotated_frame = self.current_frame.copy() if self.current_frame is not None else None
            return
        
        try:
            # Load the image
            image = self.get_current_frame()
            
            # Create annotated frame (copy of original for drawing)
            self.annotated_frame = image.copy()

            # Convert the image to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)

            # Detect the markers
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.parameters)

            # Draw detected markers (green)
            if ids is not None and len(ids) > 0:
                cv2.aruco.drawDetectedMarkers(self.annotated_frame, corners, ids, (0, 255, 0))
                print(f"Detected markers: {ids.flatten()}")
            
            # Draw rejected candidates (red)
            if len(rejected) > 0:
                cv2.aruco.drawDetectedMarkers(self.annotated_frame, rejected, borderColor=(0, 0, 255))
                print(f"Rejected candidates: {len(rejected)}")
            
            # Add status text
            status_text = f"Detected: {len(ids) if ids is not None else 0}, Rejected: {len(rejected)}"
            cv2.putText(self.annotated_frame, status_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if ids is None or len(ids) == 0:
                print("No markers detected")
                
        except Exception as e:
            print(f"ArUco detection error: {e}")
            self.annotated_frame = self.current_frame.copy() if self.current_frame is not None else None
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame"""
        return self.current_frame
    
    def get_annotated_frame(self) -> Optional[np.ndarray]:
        """Get the frame with ArUco detection annotations"""
        return self.annotated_frame if self.annotated_frame is not None else self.current_frame
    
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
