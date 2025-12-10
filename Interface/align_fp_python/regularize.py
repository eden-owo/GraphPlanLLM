import numpy as np
from shapely.geometry import box as Box
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import networkx as nx 

# Requires networkx for graph logic or custom implementation
# networkx is likely available or easy to implement simple indgree sort

def find_room_order_nx(adj_matrix):
    """
    adj_matrix: (N, N) boolean where M[i,j] = True means edge i->j
    Returns: list of indices
    """
    n = adj_matrix.shape[0]
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    
    for i in range(n):
        for j in range(n):
            if adj_matrix[i, j]:
                G.add_edge(i, j)
                
    order = []
    
    # Topological sort-ish logic from Matlab:
    # "D = indegree(G); c = find(D==0); pick one, remove, repeat."
    # If c is empty (cycle), break cycle?
    # Matlab: if isempty(c), idx = find(D==1), c = setdiff(idx, order) -> pick one?
    # Actually Matlab code handles cycles by picking D=1?
    
    # Custom implementation to match Matlab exactly involving dynamic removal
    nodes = list(range(n))
    G_temp = G.copy()
    
    while len(nodes) > 0:
        in_degrees = dict(G_temp.in_degree())
        # Filter for nodes still in graph (G_temp handles this)
        
        candidates = [node for node, deg in in_degrees.items() if deg == 0]
        
        if not candidates:
            # Matlab fallback: idx = find(D==1)
            candidates = [node for node, deg in in_degrees.items() if deg == 1]
            if not candidates:
                 # Fallback to any? Matlab doesn't specify check for D>1
                 candidates = list(in_degrees.keys())
                 
        # pick candidates
        # Matlab picks all c? "for j = 1:length(c) ... remove c"
        # Yes, processes all candidates found in this step
        
        # Sort candidates to be deterministic (Matlab uses indices)
        candidates.sort()
        
        for c in candidates:
            order.append(c)
            if c in nodes:
                nodes.remove(c)
            if G_temp.has_node(c):
                G_temp.remove_node(c)
                
    return np.array(order)

def regularize_fp(box, boundary, r_type):
    """
    box: (N, 4)
    boundary: arrays
    r_type: (N,)
    """
    box = np.array(box, dtype=float)
    n = len(box)
    
    # 1. Use boundary to crop
    if boundary.shape[1] >= 4:
        is_new = boundary[:, 3].astype(bool)
        boundary_pts = boundary[~is_new, :3] 
    else:
        boundary_pts = boundary[:, :3]
        
    poly_boundary = Polygon(boundary_pts[:, :2])
    if not poly_boundary.is_valid:
        poly_boundary = poly_boundary.buffer(0)
        
    for i in range(n):
        poly_room = Box(*box[i])
        inter = poly_boundary.intersection(poly_room)
        
        if inter.is_empty:
            print(f'Room {i} outside building!')
        else:
            block_bounds = inter.bounds
            box[i] = block_bounds 
            
    # 2. Overlap check for order
    order_m = np.zeros((n, n), dtype=bool)
    for i in range(n):
        poly_room1 = Box(*box[i])
        area1 = poly_room1.area
        for j in range(i+1, n):
            poly_room2 = Box(*box[j])
            area2 = poly_room2.area
            
            inter = poly_room1.intersection(poly_room2)
            if not inter.is_empty and inter.area > 1e-6: # Tolerance
                if area1 <= area2:
                    order_m[i, j] = True
                else:
                    order_m[j, i] = True
                    
    order = np.arange(n)
    if np.any(order_m):
        order = find_room_order_nx(order_m)
        
    # Matlab reverse order: order = order(end:-1:1)
    order = order[::-1]
    
    # 3. Gap filling
    living_idx = np.where(r_type == 0)[0]
    if len(living_idx) > 0:
        living_idx = living_idx[0]
    else:
        living_idx = 0 # Default?
        
    # Subtract all non-living rooms from boundary
    subtracted_boundary = poly_boundary
    
    for i in range(n):
        if i != living_idx:
            # Check for empty box (0 dim)
            if box[i, 0] == box[i, 2] or box[i, 1] == box[i, 3]:
                print(f'Empty box {i}')
                continue
                
            poly_room = Box(*box[i])
            subtracted_boundary = subtracted_boundary.difference(poly_room)

    living_poly = Box(*box[living_idx])
    
    gap = subtracted_boundary
    
    # Process gaps
    # gap can be MultiPolygon or Polygon
    gap_regions = []
    if isinstance(gap, Polygon):
        gap_regions = [gap]
    elif isinstance(gap, MultiPolygon):
        gap_regions = list(gap.geoms)
        
    if len(gap_regions) == 1:
        # Assign unique gap to living room
        x_limit = gap_regions[0].bounds
        box[living_idx] = x_limit # Matlab: [x1 y1 x2 y2]
        
    else:
        # Multiple gaps
        # Assign each to closest or overlapping room
        
        # Precompute overlap with living room
        # And distances
        
        # Logic: 
        # Check intersection with living poly (original living box)
        # Find closest room center
        
        # First finalize current living room box is not updated yet? 
        # Matlab uses 'livingPoly' from original box for intersection check
        
        # We need to update boxes. Matlab does it greedily per region?
        # No, it iterates regions, finds best room, then updates.
        # But if multiple gaps assigned to same room, we union them? 
        # Matlab: "box(closeRoomIdx(k),:) = boundingbox(union(room, region{k}))"
        # So it updates iteratively.
        
        pass 
        # Let's verify Matlab loop
        # It calculates assignment for ALL regions first? 
        # No, closeRoomIdx is array. 
        # Then loop k=1:length.. apply update.
        # Since box is updated in loop, subsequent unions use updated box?
        # "room = polyshape(box(closeRoomIdx(k)...))" -> Yes.
        
        overlap_areas = []
        close_room_indices = []
        
        for k, region in enumerate(gap_regions):
            area_ov = 0
            if region.intersects(living_poly):
                area_ov = region.intersection(living_poly).area
            overlap_areas.append(area_ov)
            
            centroid = region.centroid
            cx, cy = centroid.x, centroid.y
            
            # Find closest room
            dist_min = 999999.0
            b_idx = 0
            
            for i in range(n):
                b = box[i]
                bcx = (b[0] + b[2]) / 2.0
                bcy = (b[1] + b[3]) / 2.0
                d = np.hypot(bcx - cx, bcy - cy)
                if d < dist_min:
                    dist_min = d
                    b_idx = i
            close_room_indices.append(b_idx)
            
        # lIdx = max(overlapArea) -> index of gap with largest overlap with living room?
        # This gap is assigned to living room (living_idx)? 
        # Matlab: [~, lIdx] = max(overlapArea); 
        # if k == lIdx -> update living_idx with region{k} bounds (replace?)
        # Matlab: "box(livingIdx,:) = [xLimit...]" - REPLACES living room box with just this gap??
        # Wait. "region{k}" in Matlab comes from gap.Vertices.
        # The Gap IS the remaining space for living room?
        # Ah, "gap = polyBoundary; ... subtract non-living ... gap is remaining".
        # So the Gap IS logically the living room (plus potentially errors).
        # We want to find the "Main" part of the gap to be the Living Room.
        # And "Small detached parts" of the gap to be assigned to nearest other rooms.
        
        max_overlap_idx = np.argmax(overlap_areas)
        
        for k, region in enumerate(gap_regions):
            if k == max_overlap_idx:
                # This is the main living room body
                # REPLACE living box with this clean region bounds
                b = region.bounds
                box[living_idx] = b
            else:
                # Fragment, merge into closest room
                target_idx = close_room_indices[k]
                target_room = Box(*box[target_idx])
                merged = target_room.union(region)
                box[target_idx] = merged.bounds
                
    return box, order
