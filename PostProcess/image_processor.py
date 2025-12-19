import cv2
import numpy as np
import base64

class ImageProcessor:
    def __init__(self):
        self.canvas_size = 256
        self.margin = 32  # Margin from edges
        # Standard door size relative to 256px canvas (heuristic)
        self.door_width = 16 

    def process_dimensions(self, width, depth):
        """
        Generate a rectangular boundary based on physical width and depth.
        
        Args:
            width (float): Physical width in meters
            depth (float): Physical depth in meters
            
        Returns:
            dict: {
                'exterior': list of points [[x,y],...],
                'door': list [x1, y1, x2, y2]
            }
        """
        aspect_ratio = width / depth
        
        # Calculate max available size inside margins
        max_draw_size = self.canvas_size - (2 * self.margin)
        
        if aspect_ratio >= 1:
            # Wider than tall
            draw_w = max_draw_size
            draw_h = max_draw_size / aspect_ratio
        else:
            # Taller than wide
            draw_h = max_draw_size
            draw_w = max_draw_size * aspect_ratio
            
        # Center the rectangle
        x_start = (self.canvas_size - draw_w) / 2
        y_start = (self.canvas_size - draw_h) / 2
        x_end = x_start + draw_w
        y_end = y_start + draw_h
        
        # Convert to integers
        x1, y1 = int(x_start), int(y_start)
        x2, y2 = int(x_end), int(y_end)
        
        # Create exterior polygon points (Clockwise)
        # Top-Left, Top-Right, Bottom-Right, Bottom-Left
        exterior = [
            [x1, y1], # Top-Left
            [x2, y1], # Top-Right
            [x2, y2], # Bottom-Right
            [x1, y2]  # Bottom-Left
        ]
        
        # Heuristic for door: Place in middle of bottom edge
        # Door segment format for Graph2Plan: [x1, y1, x2, y2]
        mid_x = int((x1 + x2) / 2)
        half_door = int(self.door_width / 2)
        
        # Ensure door fits
        door_x1 = max(x1, mid_x - half_door)
        door_x2 = min(x2, mid_x + half_door)
        door_y = y2 
        
        door = [door_x1, door_y, door_x2, door_y]
        
        return {
            'exterior': exterior,
            'door': door
        }

    def process_image(self, image_bytes):
        """
        Process uploaded image to find boundary.
        (To be implemented: OpenCV logic here)
        """
        # Placeholder for now, to be filled in next step if needed
        pass
