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
import csv
import os
import signal
import sys

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
        
        self.marker_world_positions = {}  # Now stores {id: {'position': [x,y,z], 'size': float}}
        layout = 1
        if layout == 0:
            for i in range(5):
                self.marker_world_positions.update({i: {
                    'position': [1.8, 1.5-(0.125+i*0.25), 0],
                    'size': 0.085
                }}) # layout 0 marker positions
        elif layout == 1:
            page_offsets_y = [0, 0.252, 0.252, 0.251, 0.246] # page offsets between page_coords y-axis
            marker_offsets = [[0,0,0], 
                              [0, 0.098, 0],
                              [0, -0.018, -0.116],
                              [0, 0.0305, -0.116],
                              [0, 0.0785, -0.116],
                              [0, 0.1265, -0.116],
                              [0, 0, -0.184],
                              [0, 0.098, -0.184]] # Marker offsets from page_coords
            
            start_coord = [1.8, 1.5-(0.035+0.037), 0.229] # Position of first page, first marker / used to find first position of first marker on each page
            page_coords = []  # Changed to list instead of numpy array
            
            # Calculate page coordinates
            cumulative_offset = 0
            for i in range(5):
                cumulative_offset += page_offsets_y[i]
                page_coord = [start_coord[0], 
                              start_coord[1] - cumulative_offset, 
                              start_coord[2]]
                page_coords.append(page_coord)
            
            num = 0
            for i in range(5):  # Pages
                start = page_coords[i]  # start is now [x,y,z]
                for j in range(8):  # Each marker per page
                    marker_pos = [start[0] + marker_offsets[j][0],
                                 start[1] - marker_offsets[j][1], 
                                 start[2] + marker_offsets[j][2]]
                    
                    # Determine marker size based on position within page
                    # First two (j=0,1) and last two (j=6,7) use 0.076, others use 0.026
                    if j in [0, 1, 6, 7]:
                        marker_size = 0.076
                    else:
                        marker_size = 0.026
                    
                    self.marker_world_positions.update({num: {
                        'position': marker_pos,
                        'size': marker_size
                    }})
                    num += 1



        
        self.marker_size = 0.085  # Size of your markers in meters (85mm)

        self.tcp = tcp
        
        # Data collection for CSV output (always enabled now)
        self.pose_data = []  # Store [x, y, yaw] coordinates
        self.collect_data = True  # Always collect data regardless of TCP status
        
        # Always enable data collection and signal handler
        print("📊 Data collection enabled - press Ctrl+C to save pose data to CSV")
        signal.signal(signal.SIGINT, self.signal_handler)
        
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
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C signal to save pose data to CSV"""
        if self.collect_data and len(self.pose_data) > 0:
            self.save_pose_data_to_csv()
        print("\n🛑 Exiting...")
        sys.exit(0)
    
    def get_next_output_filename(self):
        """Get the next available output filename (output/output1.csv, output/output2.csv, etc.)"""
        # Create output directory if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        counter = 1
        while True:
            filename = os.path.join(output_dir, f"output{counter}.csv")
            if not os.path.exists(filename):
                return filename
            counter += 1
    
    def save_pose_data_to_csv(self):
        """Save collected pose data to CSV file"""
        if not self.pose_data:
            print("📝 No pose data to save")
            return
        
        filename = self.get_next_output_filename()
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['x', 'y', 'yaw'])
                # Write data
                writer.writerows(self.pose_data)
            print(f"💾 Saved {len(self.pose_data)} pose entries to {filename}")
        except Exception as e:
            print(f"❌ Error saving CSV file: {e}")

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
                
            except Exception as e:
                print(f"Failed to connect to simulator: {e}")
        except Exception as e:     
            print(f"Failed to set up tcp: {e}")

    def get_marker_corners_3d(self, marker_center, marker_size):
        """Get 4 corners of marker in 3D world coordinates"""
        half_size = marker_size / 2
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

        # Shift point to center of car
        x = x - 50*math.cos(orientation)
        y = y + 50*math.sin(orientation)

        message = f"{x:.3f},{y:.3f},{orientation:.3f}"
        try:
            self.client_socket.send(message.encode("utf-8"))
            print(f"📡 Sent: {message}")
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            print(f"🔌 Connection closed by simulator - data sent successfully")
            # Connection is closed, which is expected behavior
            # Remove the client socket reference to avoid further attempts
            if hasattr(self, 'client_socket'):
                delattr(self, 'client_socket')


    def get_camera_angle_from_rtvec(self, rvec, tvec):
        """Extract camera yaw angle (rotation around Z-axis) for 2D top-down view"""
        R, _ = cv2.Rodrigues(rvec)

        yaw = math.degrees(math.atan2(R[2,0], R[2,1]))
        # Adjust to fit my coordinates in sim
        yaw = -yaw +90
        return yaw
    
    def get_camera_position_from_multiple_markers(self):
        """Calculate camera position using multiple detected markers with PnP"""
        if self.corners is None or self.ids is None:
            return None
            
        object_points = []
        image_points = []
        
        for i, marker_id in enumerate(self.ids.flatten()):
            if marker_id in self.marker_world_positions:
                # Get the 4 corners of this marker in world coordinates
                marker_info = self.marker_world_positions[marker_id]
                marker_corners_3d = self.get_marker_corners_3d(marker_info['position'], marker_info['size'])
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
                    camera_angle = self.get_camera_angle_from_rtvec(rvec, tvec)
                    
                    # Store valid position and angle
                    self.last_valid_pos = [camera_pos[0], camera_pos[1]] # Ignoring z component
                    self.last_valid_angle = camera_angle # Use the angle as calculated
                    
                    x = camera_pos[0]-0.1*math.cos(math.radians(camera_angle))
                    y = camera_pos[1]-0.1*math.sin(math.radians(camera_angle))
                    # Always collect pose data regardless of TCP status
                    # Scale coordinates and transform y-axis
                    x_scaled = x * RATIO_MTS
                    y_scaled = y * RATIO_MTS
                    y_transformed = SCREENHEIGHT - y_scaled
                    self.pose_data.append([x_scaled, y_transformed, self.last_valid_angle])

                    print(f"Camera position: X={x:.3f}m, Y={y:.3f}m, Z={camera_pos[2]:.3f}m") # Convert to center of car position
                    print(f"Camera angle: {self.last_valid_angle:.1f}°")
                    print(f"📊 Collected {len(self.pose_data)} pose entries")
                    
                    # Send pose data via TCP if connected
                    if self.tcp and hasattr(self, 'client_socket'):
                        try:
                            self.convert_and_send()
                        except Exception as e:
                            print(f"🔌 TCP connection lost: {e}")
                            # Remove client socket reference to stop further attempts
                            if hasattr(self, 'client_socket'):
                                delattr(self, 'client_socket')
                        
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
            marker_corners = self.get_marker_corners()
            marker_ids = self.get_marker_ids()
            if marker_corners is None or marker_ids is None:
                return

            # Estimate the pose for each detected marker
            for i, corners in enumerate(marker_corners):
                marker_id = marker_ids[i][0]  # Extract the actual ID
                if marker_id in self.marker_world_positions:
                    marker_length = self.marker_world_positions[marker_id]['size']
                else:
                    marker_length = self.marker_size  # Fallback to default size
                
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
