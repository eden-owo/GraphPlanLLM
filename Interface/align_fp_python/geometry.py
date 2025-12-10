import numpy as np
from shapely.geometry import box as Box
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

def get_entrance_space(door_seg, door_ori, threshold):
    """
    door_seg: numpy array or list of shape (2, 2) [[x1, y1], [x2, y2]]
    door_ori: int 0-3
    threshold: float
    """
    seg = np.array(door_seg)
    xmin = min(seg[:, 0])
    xmax = max(seg[:, 0])
    ymin = min(seg[:, 1])
    ymax = max(seg[:, 1])
    
    door_box = [xmin, ymin, xmax, ymax]
    
    if door_ori == 0:
        door_box[3] += threshold
    elif door_ori == 1:
        door_box[0] -= threshold
    elif door_ori == 2:
        door_box[1] -= threshold
    elif door_ori == 3:
        door_box[2] += threshold
        
    return door_box

def find_close_seg(box_arr, boundary):
    """
    box: [x1, y1, x2, y2]
    boundary: numpy array (N, 4) [x, y, dir, isNew]
    
    Returns:
        closed_seg: list of 4 closest segments (one for each side of box)
        dist_seg: list of 4 distances
        idx: list of indices of the segments in the boundary array
    """
    
    if boundary.shape[1] >= 4:
        is_new = boundary[:, 3].astype(bool)
        boundary_pts = boundary[~is_new, :3] # x, y, dir
    else:
        boundary_pts = boundary[:, :3]

    # Construct segments
    # Data is like: [x, y, dir]
    # Segments connect point i to i+1
    p1 = boundary_pts[:, :2] # x, y
    p2 = np.roll(boundary_pts[:, :2], -1, axis=0) # next points
    dirs = boundary_pts[:, 2] # directions
    
    # Check if vertical (mod(dir, 2) == 1)
    is_vert = (dirs % 2 == 1)
    
    # vSeg 
    v_seg_indices = np.where(is_vert)[0]
    v_seg = np.column_stack([p1[v_seg_indices], p2[v_seg_indices], dirs[v_seg_indices], v_seg_indices])
    
    # hSeg
    h_seg_indices = np.where(~is_vert)[0]
    h_seg = np.column_stack([p1[h_seg_indices], p2[h_seg_indices], dirs[h_seg_indices], h_seg_indices])
    
    closed_seg = np.full(4, 256.0) 
    dist_seg = np.full(4, 256.0)
    idx_out = np.zeros(4, dtype=int)
    
    bx1, by1, bx2, by2 = box_arr
    
    # Check vertical segments
    for i in range(len(v_seg)):
        seg = v_seg[i]
        # seg: x1, y1, x2, y2, dir, idx
        sx = seg[0] # Vertical has const x
        sy1 = min(seg[1], seg[3])
        sy2 = max(seg[1], seg[3])
        
        # Check y-overlap
        vdist = 0
        if sy2 <= by1:
            vdist = by1 - sy2
        elif sy1 >= by2:
            vdist = sy1 - by2
            
        hd1 = bx1 - sx
        hd2 = bx2 - sx
        
        dist1 = np.linalg.norm([hd1, vdist])
        dist3 = np.linalg.norm([hd2, vdist])
        
        # Left side of box (x1) vs Segment
        if dist1 < dist_seg[0] and dist1 <= dist3 and hd1 > 0:
            dist_seg[0] = dist1
            idx_out[0] = int(seg[5])
            closed_seg[0] = sx
            
        # Right side of box (x2) vs Segment
        elif dist3 < dist_seg[2] and hd2 < 0:
            dist_seg[2] = dist3
            idx_out[2] = int(seg[5])
            closed_seg[2] = sx

    # Check horizontal segments
    for i in range(len(h_seg)):
        seg = h_seg[i]
        sy = seg[1] # Horizontal has const y
        sx1 = min(seg[0], seg[2])
        sx2 = max(seg[0], seg[2])
        
        # Check x-overlap
        hdist_gap = 0
        if sx2 <= bx1:
            hdist_gap = bx1 - sx2
        elif sx1 >= bx2:
            hdist_gap = sx1 - bx2
            
        vd1 = by1 - sy
        vd2 = by2 - sy
        
        dist2 = np.linalg.norm([vd1, hdist_gap])
        dist4 = np.linalg.norm([vd2, hdist_gap])
        
        # Top side of box (y1) vs Segment
        if dist2 <= dist4 and dist2 < dist_seg[1] and vd1 > 0:
            dist_seg[1] = dist2
            idx_out[1] = int(seg[5])
            closed_seg[1] = sy
            
        # Bottom side of box (y2) vs Segment
        elif dist4 < dist_seg[3] and vd2 < 0:
            dist_seg[3] = dist4
            idx_out[3] = int(seg[5])
            closed_seg[3] = sy
            
    return closed_seg, dist_seg, idx_out

def shrink_box(room_poly, entrance_poly, door_orient):
    """
    room_poly: shapely.geometry.Polygon
    entrance_poly: shapely.geometry.Polygon
    door_orient: int
    
    Returns:
        box: [x1, y1, x2, y2]
    """
    pg = room_poly.difference(entrance_poly)
    
    if pg.is_empty:
        return room_poly.bounds
        
    if isinstance(pg, Polygon):
        return pg.bounds
        
    if isinstance(pg, MultiPolygon):
        parts = list(pg.geoms)
        parts.sort(key=lambda p: p.area, reverse=True)
        return parts[0].bounds
        
    return room_poly.bounds

def align_with_boundary(box_arr, boundary, threshold, r_type):
    """
    box_arr: numpy array (N, 4)
    boundary: numpy array
    threshold: float
    r_type: numpy array
    """
    box_arr = np.array(box_arr, dtype=float)
    temp_box = box_arr.copy()
    updated = np.zeros(box_arr.shape, dtype=bool)
    n = len(box_arr)
    
    constraint = [] 
    
    # 1. Align walls
    for i in range(n):
        closed_seg, dist_seg, _ = find_close_seg(box_arr[i], boundary)
        
        for j in range(4):
            if dist_seg[j] <= threshold:
                box_arr[i, j] = closed_seg[j]
                updated[i, j] = True
                constraint.append([i, j, closed_seg[j]])
                
    # 2. Check door blocking
    if boundary.shape[0] >= 2:
        door_seg = boundary[0:2, 0:2] 
        door_ori = boundary[0, 2]
        
        entrance_box = get_entrance_space(door_seg, door_ori, threshold)
        entrance_poly = Box(*entrance_box)
        
        for i in range(n):
            if r_type[i] != 10 and r_type[i] != 0:
                room_poly = Box(*box_arr[i])
                if entrance_poly.intersects(room_poly):
                    new_bounds = shrink_box(room_poly, entrance_poly, door_ori)
                    box_arr[i] = new_bounds
                    if not np.array_equal(box_arr[i], temp_box[i]):
                        updated[i, :] = True
                        
    return constraint, box_arr, updated
