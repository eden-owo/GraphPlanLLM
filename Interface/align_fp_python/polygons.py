import numpy as np
from shapely.geometry import box as Box
from shapely.geometry import Polygon, MultiPolygon

def get_room_boundary(box, boundary, order):
    """
    box: (N, 4)
    boundary: array
    order: array of indices (N,)
    
    Returns:
        new_box: (N, 4) updated bounds
        r_boundary: list of vertex arrays (N,)
    """
    box = np.array(box, dtype=float)
    n = len(box)
    
    if boundary.shape[1] >= 4:
        is_new = boundary[:, 3].astype(bool)
        boundary_pts = boundary[~is_new, :3] 
    else:
        boundary_pts = boundary[:, :3]
        
    poly_boundary = Polygon(boundary_pts[:, :2])
    if not poly_boundary.is_valid:
        poly_boundary = poly_boundary.buffer(0)
        
    polys = []
    for i in range(n):
        if np.isnan(box[i]).any():
            polys.append(Polygon())
        else:
            try:
                polys.append(Box(*box[i]))
            except Exception:
                polys.append(Polygon())
        
    new_box = box.copy()
    r_boundary = [None] * n
    
    for i in range(n):
        idx = int(order[i])
        
        # Intersect with boundary
        r_poly = poly_boundary.intersection(polys[idx])
        
        # Subtract lower priority rooms (j > i in order list)
        for j in range(i + 1, n):
            j_idx = int(order[j])
            if not polys[j_idx].is_empty:
                 r_poly = r_poly.difference(polys[j_idx])
                 
        # Output vertices
        # Handle MultiPolygon (take largest? or all?)
        # Matlab stores Vertices. If multipolygon, might be tricky.
        # Matlab `rPoly.Vertices` usually returns all vertices or just main loop?
        # Assuming Polygon. If Multi, standard practice is union of coords or list?
        # For JSON output, usually a single list of point paths is expected.
        # But `views.py` just iterates `rBoundary`.
        
        if r_poly.is_empty:
             r_boundary[idx] = []
             continue
             
        if isinstance(r_poly, MultiPolygon):
            # Find largest part for bounds
            parts = list(r_poly.geoms)
            if not parts:
                r_boundary[idx] = []
                continue
            
            # For bounds: envelope of all?
            # Matlab `boundingbox(rPoly)` returns box enclosing all? Yes.
            combined_bounds = r_poly.bounds
            new_box[idx] = combined_bounds
            
            # For vertices: we might simply take the largest part or return list of lists?
            # Views.py: `fp_end.data.rBoundary = [np.array(rb) for rb in rBoundary]`
            # It expects array of points.
            # If MultiPolygon, we likely only want the main room shape.
             
            largest = max(parts, key=lambda p: p.area)
            if largest.exterior:
                 coords = list(largest.exterior.coords)
                 # Remove last duplicate point if present (shapely closes usually)
                 if coords[0] == coords[-1]:
                     coords.pop()
                 r_boundary[idx] = coords
            else:
                 r_boundary[idx] = []
                 
        elif isinstance(r_poly, Polygon):
             new_box[idx] = r_poly.bounds
             if r_poly.exterior:
                 coords = list(r_poly.exterior.coords)
                 if coords[0] == coords[-1]:
                     coords.pop()
                 r_boundary[idx] = coords
             else:
                 r_boundary[idx] = []
    
    # Ensure no None values remain (for savemat compatibility)
    for i in range(n):
        if r_boundary[i] is None:
            r_boundary[i] = []
                 
    return new_box, r_boundary
