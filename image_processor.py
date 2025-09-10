#!/usr/bin/env python3
"""
ImageProcessor class for handling frame storage and ArUco detection
Simplified version without grayscale display functionality
"""

from typing import List, Optional
import numpy as np
import cv2
import threading
import socket
import math

# Camera calibration parameters
mtx = np.array([[1.31210204e+03, 0.00000000e+00, 6.23587581e+02],
 [0.00000000e+00, 1.32186888e+03, 3.29367318e+02],
 [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])

# Camera distortion matrix
dist = np.array([ 0.13285292,  0.60199342, -0.01296075, -0.00628914, -3.23261949]) 

SCREENWIDTH = 900 # in pixels
SCREENHEIGHT = 750 # in pixels
MAPWIDTH = 1.8 # in m
MAPHEIGHT = 1.5 # in m
RATIO_MTS = SCREENHEIGHT/MAPHEIGHT # map to screen conversion ratio

class ImageProcessor:
    def __init__(self, camera_mtx=None, camera_dist=None, headless=False, tcp=False):
        """Initialize ImageProcessor with frame storage"""
        self.current_frame = None
        self.frames = []  # List to store recent frames
        self.num_frames = 2
        self.annotated_frame = None  # Frame with ArUco annotations
        self.headless = headless  # If True, skip visualization processing
        self.corners = None
        self.ids = None
        self.last_valid_pos = [0,0] # Store camera position (x,y) (normal cartesian, not python!!)
        self.last_valid_angle = 0  # Store camera angle in degrees

        # Set camera calibration parameters
        self.mtx = camera_mtx if camera_mtx is not None else mtx
        self.dist = camera_dist if camera_dist is not None else dist
        
        self.marker_world_positions = {}
        for i in range(5):
            self.marker_world_positions.update({i: [1.8, 1.5-(0.125+i*0.25),0]}) # layout 1 marker positions
        
        self.marker_size = 0.085  # Size of your markers in meters (85mm)

        self.tcp = tcp
        if self.tcp: # Only try to start the tcp server if specified
            self.setup_tcp()
        else:
            print("TCP communication disabled, continuing...")

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
    
    def setup_tcp(self):
        try:
            print("TCP Sender - Starting server...")
            print("Please start simulator to continue!")
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try: 
                self.server_socket.bind((socket.gethostname(), 1234))
                self.server_socket.listen(5)
                print(f"Server listening on {socket.gethostname()}:1234")
                print("Waiting for client connections...")

                # Accept client connection (Will hang until sim is connected!)
                self.client_socket, address = self.server_socket.accept()
                print(f"Connection from {address} has been established!")
                
                # Send a test message to confirm connection
                #test_message = "50,69,420"
                #self.client_socket.send(test_message.encode("utf-8"))
                #print(f"Sent test message: {test_message}")
                
            except Exception as e:
                print(f"Failed to connect to simulator: {e}")
        except Exception as e:     
            print(f"Failed to set up tcp: {e}")
    
    def send_pose_data(self):
        """Send current pose data to connected client"""
        if hasattr(self, 'client_socket'):
            try:
                # Format: x,y,orientation
                message = f"{self.last_valid_pos[0]:.3f},{self.last_valid_pos[1]:.3f},{self.last_valid_angle:.1f}"
                self.client_socket.send(message.encode("utf-8"))
                print(f"📡 Sent: {message}")
            except Exception as e:
                print(f"❌ Failed to send pose data: {e}")


    def get_marker_corners_3d(self, marker_center):
        """Get 4 corners of marker in 3D world coordinates"""
        half_size = self.marker_size / 2
        # Corner order MUST match OpenCV ArUco detection: top-left, top-right, bottom-right, bottom-left
        return [
            [marker_center[0], marker_center[1] + half_size, marker_center[2] + half_size], # top-left
            [marker_center[0], marker_center[1] - half_size, marker_center[2] + half_size], # top-right
            [marker_center[0], marker_center[1] - half_size, marker_center[2] - half_size], # bottom-right
            [marker_center[0], marker_center[1] + half_size, marker_center[2] - half_size]  # bottom-left
        ]
    
    def convert_and_send(self):
        x = self.last_valid_pos[0]*RATIO_MTS
        y = (MAPHEIGHT - self.last_valid_pos[1])*RATIO_MTS
        orientation = math.radians(self.last_valid_angle)

        message = f"{x},{y},{orientation}"
        self.client_socket.send(message.encode("utf-8"))
        print(f"Sent test message: {message}")


    def get_camera_angle_from_rvec(self, rvec):
        """Extract camera yaw angle (rotation around Z-axis) for 2D top-down view"""
        # Convert rotation vector to rotation matrix
        R, _ = cv2.Rodrigues(rvec)
        
        # Extract only the yaw angle (rotation around Z-axis) for 2D navigation
        # This represents the direction the camera is facing in the XY plane
        yaw_radians = np.arctan2(R[1,0], R[0,0])
        
        # Convert to degrees and normalize to [0, 360)
        yaw_degrees = np.degrees(yaw_radians)
        if yaw_degrees < 0:
            yaw_degrees += 360
            
        return yaw_degrees
    
    def get_camera_position_from_multiple_markers(self):
        """Calculate camera position using multiple detected markers with PnP"""
        if self.corners is None or self.ids is None:
            return None
            
        object_points = []
        image_points = []
        
        for i, marker_id in enumerate(self.ids.flatten()):
            if marker_id in self.marker_world_positions:
                # Get the 4 corners of this marker in world coordinates
                marker_corners_3d = self.get_marker_corners_3d(self.marker_world_positions[marker_id])
                object_points.extend(marker_corners_3d)
                
                # Get corresponding 2D points in image
                image_points.extend(self.corners[i][0])
        
        if len(object_points) >= 4:  # Need at least 4 points (1 marker minimum)
            object_points = np.array(object_points, dtype=np.float32)
            image_points = np.array(image_points, dtype=np.float32)
            
            # Use original camera matrix and distortion coefficients
            success, rvec, tvec = cv2.solvePnP(object_points, image_points, self.mtx, self.dist)
            
            if success:
                # Convert to camera position in world coordinates
                R, _ = cv2.Rodrigues(rvec)
                camera_pos = -R.T @ tvec.flatten()
                return camera_pos, rvec, tvec
        
        return None, None, None
        
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
        """Detect ArUco markers and create annotated frame for visualization"""
        if self.current_frame is None or not self.aruco_available:
            if not self.headless:
                self.annotated_frame = self.current_frame.copy() if self.current_frame is not None else None
            return
        
        try:
            # Load the image
            image = self.get_current_frame()
            
            # Create annotated frame only if not headless
            if not self.headless:
                self.annotated_frame = image.copy()

            # Convert the image to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)

            # Detect the markers
            self.corners, self.ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.parameters)

            # Only do visualization if not headless
            if not self.headless:
                # Draw detected markers (green)
                if self.ids is not None and len(self.ids) > 0:
                    cv2.aruco.drawDetectedMarkers(self.annotated_frame, self.corners, self.ids, (0, 255, 0))
                
                # Draw rejected candidates (red)
                if len(rejected) > 0:
                    cv2.aruco.drawDetectedMarkers(self.annotated_frame, rejected, borderColor=(0, 0, 255))
                
                # Add status text
                status_text = f"Detected: {len(self.ids) if self.ids is not None else 0}, Rejected: {len(rejected)}"
                cv2.putText(self.annotated_frame, status_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Always print detection results (terminal output)
            if self.ids is not None and len(self.ids) > 0:
                print(f"Detected markers: {self.ids.flatten()}")
                
                # Calculate camera position using multiple markers
                camera_pos, rvec, tvec = self.get_camera_position_from_multiple_markers()
                if camera_pos is not None:
                    # Extract camera angle from rotation vector
                    camera_angle = self.get_camera_angle_from_rvec(rvec)
                    
                    # Store valid position and angle
                    self.last_valid_pos = [camera_pos[0], camera_pos[1]] # Ignoring z component
                    self.last_valid_angle = -(camera_angle -90) # adjusting to fit normal cartesian
                    
                    print(f"Camera position: X={camera_pos[0]:.3f}m, Y={camera_pos[1]:.3f}m, Z={camera_pos[2]:.3f}m")
                    print(f"Camera angle: {self.last_valid_angle:.1f}°")
                    
                    # Send pose data via TCP if connected
                    if self.tcp and hasattr(self, 'client_socket'):
                        self.convert_and_send()
                        
                else:
                    print("Camera position: Unable to calculate (need markers with known positions)")
            else:
                print("No markers detected")
            
            if len(rejected) > 0:
                print(f"Rejected candidates: {len(rejected)}")

            self.poseEstimation()
            
        except Exception as e:
            print(f"ArUco detection error: {e}")
            if not self.headless:
                self.annotated_frame = self.current_frame.copy() if self.current_frame is not None else None

    def poseEstimation(self):
        """Estimate the pose of detected ArUco markers"""
        if self.current_frame is None or not self.aruco_available:
            return

        try:
            # Get the camera matrix and distortion coefficients
            camera_matrix = self.mtx
            dist_coeffs = self.dist

            # Get the 3D points of the ArUco markers
            marker_length = self.marker_size  # Length of the marker's side (in mm)
            marker_corners = self.get_marker_corners()
            if marker_corners is None:
                return

            # Estimate the pose for each detected marker
            for corners in marker_corners:
                rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corners, marker_length, camera_matrix, dist_coeffs)
                if not self.headless:
                    self.draw_pose_axes(rvec, tvec)

        except Exception as e:
            print(f"Pose estimation error: {e}")

    def draw_pose_axes(self, rvec, tvec):
        """Draw the axes for the estimated pose"""
        if self.annotated_frame is None:
            return

        # Define the axis length (in m)
        axis_length = 0.1

        # Get the camera matrix and distortion coefficients
        camera_matrix = self.mtx
        dist_coeffs = self.dist

        # Draw the axes
        cv2.aruco.drawAxis(self.annotated_frame, camera_matrix, dist_coeffs, rvec, tvec, axis_length)

    def get_marker_corners(self):
        """Get the corners of detected ArUco markers"""
        return self.corners if self.corners is not None else []

    def get_marker_ids(self):
        """Get the IDs of detected ArUco markers"""
        return self.ids if self.ids is not None else []

    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame"""
        return self.current_frame
    
    def get_annotated_frame(self):
        """Get the frame with ArUco detection annotations"""
        if self.headless:
            return self.current_frame  # Return raw frame in headless mode
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
