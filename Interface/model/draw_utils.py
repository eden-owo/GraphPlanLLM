
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def get_room_color(room_name):
    """Ref: buttonEvent_wizard.js roomcolor function"""
    colors = {
        "LivingRoom": (200/255, 200/255, 200/255),
        "MasterRoom": (253/255, 244/255, 171/255),
        "Kitchen": (234/255, 216/255, 214/255),
        "Bathroom": (205/255, 233/255, 252/255),
        "DiningRoom": (244/255, 242/255, 229/255),
        "ChildRoom": (253/255, 244/255, 171/255),
        "StudyRoom": (253/255, 244/255, 171/255),
        "SecondRoom": (253/255, 244/255, 171/255),
        "GuestRoom": (253/255, 244/255, 171/255),
        "Balcony": (208/255, 216/255, 135/255),
        "Entrance": (244/255, 242/255, 229/255),
        "Storage": (249/255, 222/255, 189/255),
        "Wall-in": (202/255, 207/255, 239/255),
        "External area": (1.0, 1.0, 1.0),
        "Exterior wall": (79/255, 79/255, 79/255),
        "Front door": (255/255, 225/255, 25/255),
        "Interior wall": (128/255, 128/255, 128/255),
        "Interior door": (1.0, 1.0, 1.0)
    }
    return colors.get(room_name, (0.8, 0.8, 0.8)) # Default gray

def draw_floorplan(data, save_path):
    """
    Draw floorplan and save to file.
    data: Dictionary from FindTraindata containing 'hsbox', 'exterior', 'door'
    """
    fig, ax = plt.subplots(figsize=(5, 5)) 
    # Determine bounds from exterior
    exterior_str = data.get('exterior', '').strip()
    points = []
    if exterior_str:
        pairs = exterior_str.split(' ')
        for p in pairs:
            if ',' in p:
                x, y = map(float, p.split(','))
                points.append([x, y])
    
    if not points:
        plt.close(fig)
        return False
        
    points = np.array(points)
    x_min, x_max = points[:, 0].min(), points[:, 0].max()
    y_min, y_max = points[:, 1].min(), points[:, 1].max()
    
    # Set limits with some padding
    padding = 20
    ax.set_xlim(x_min - padding, x_max + padding)
    ax.set_ylim(y_min - padding, y_max + padding) # Matplotlib originates at bottom-left, SVG usually top-left.
    # Note: SVGs from frontend usually have +Y down. Matplotlib has +Y up.
    # We might need to invert Y axis to match visual look, or just plot as is.
    # Let's verify coordinate system. Data usually 0-256 range.
    # If we invert Y, we need `ax.invert_yaxis()`
    ax.invert_yaxis()
    
    ax.set_aspect('equal')
    ax.axis('off') # Hide axes
    
    # Draw Exterior Polygon
    poly = patches.Polygon(points, closed=True, 
                          edgecolor=get_room_color("Exterior wall"), 
                          facecolor='none', 
                          linewidth=4) # Using logic from frontend: stroke-width 6 (relative to view)
    ax.add_patch(poly)

    # Draw Rooms
    # hsbox structure: [[[x1, y1, x2, y2], [label]], ...]
    interior_wall_color = get_room_color("Interior wall")
    if 'hsbox' in data:
        for box_item in data['hsbox']:
            coords = box_item[0]
            label = box_item[1][0]
            x1, y1, x2, y2 = float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])
            
            width = x2 - x1
            height = y2 - y1
            
            rect = patches.Rectangle((x1, y1), width, height,
                                    linewidth=2,
                                    edgecolor=interior_wall_color,
                                    facecolor=get_room_color(label))
            ax.add_patch(rect)
            
    # Draw Door
    # door string: "x1,y1,x2,y2"
    if 'door' in data:
        d = list(map(float, data['door'].split(',')))
        door_line = plt.Line2D([d[0], d[2]], [d[1], d[3]], 
                              color=get_room_color("Front door"), 
                              linewidth=4) # Front door thick line
        ax.add_line(door_line)

    # Save
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0, dpi=72)
    plt.close(fig)
    return True
