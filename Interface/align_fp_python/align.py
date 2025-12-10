import numpy as np
from .geometry import align_with_boundary, get_entrance_space
from .neighbors import align_neighbor
from .regularize import regularize_fp
from .polygons import get_room_boundary

def align_fp(boundary, r_box, r_type, r_edge, fp=None, threshold=18.0, draw_result=False):
    """
    boundary: (N, 4) or list
    r_box: (N, 4)
    r_type: (N,)
    r_edge: (M, 3) [u, v, type]
    """
    
    print("DEBUG: align_fp_python called")
    # Ensure inputs are numpy arrays
    boundary = np.array(boundary, dtype=float)
    r_box = np.array(r_box, dtype=float)
    r_type = np.array(r_type, dtype=int).flatten()
    r_edge = np.array(r_edge, dtype=float)
    
    # Matlab logic: move living room edges to end?
    # livingIdx = find(rType==0);
    # idx = rEdge(:,1) == livingIdx-1 | rEdge(:,2) == livingIdx-1;
    # rEdge = rEdge(~idx, :); 
    # Matlab logic literally REMOVES living room edges? "rEdge = rEdge(~idx, :)"
    # Code comment says: "move ... to the end", commented out code: "rEdge = [a; b]". 
    # But ONLY "rEdge = rEdge(~idx, :)" is active.
    # So it REMOVES edges connected to Living Room (Index 0 in python terms if rType==0 is Living Room).
    # Matlab indices are 1-based. livingIdx is index.
    # But rType has values. "livingIdx = find(rType==0)".
    # If rType[k] == 0, then k is index.
    
    living_indices = np.where(r_type == 0)[0]
    if len(living_indices) > 0:
        living_idx = living_indices[0] # Python 0-based index
        
        # rEdge has indices. In python rewrite we assume 0-based indices in rEdge?
        # Inputs from test.py usually come from file/net. 
        # In test.py: "Edge = [[float(u), float(v), float(type2)] for u, v, type2 in rEdge]"
        # If original rEdge from network was 0-based, test.py passes it on.
        # Matlab expects 1-based for computation maybe?
        # But my python `align_neighbor` assumes 0-based.
        # Let's assume standard input is 0-based index.
        
        # Identify edges connected to living room
        mask = (r_edge[:, 0] == living_idx) | (r_edge[:, 1] == living_idx)
        
        # Remove them as per Matlab active code
        r_edge = r_edge[~mask]
    
    # 1. Align with boundary (Optional in Matlab flow but part of `option #1`)
    # Matlab calls: [~, newBox, updated] = align_with_boundary(rBox, boundary, threshold, rType);
    _, new_box, updated = align_with_boundary(r_box, boundary, threshold, r_type)
    
    # 2. Align neighbors
    # [~, newBox, ~] = align_neighbor(newBox, rEdge, updated, threshold+6);
    _, new_box, _ = align_neighbor(new_box, r_edge, updated, threshold + 6.0)
    
    # 3. Regularize
    # [newBox, order] = regularize_fp(newBox, boundary, rType);
    new_box, order = regularize_fp(new_box, boundary, r_type)
    
    # 4. Generate polygons
    # [newBox, rBoundary] = get_room_boundary(newBox, boundary, order);
    new_box, r_boundary = get_room_boundary(new_box, boundary, order)
    
    # Return matches Matlab align_fp: [newBox, order, rBoundary]
    return new_box, order, r_boundary
