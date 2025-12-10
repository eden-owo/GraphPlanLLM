import numpy as np

def align_adjacent_room3(box, temp_box, updated, r_type, threshold):
    """
    box: (2, 4) [[x1, y1, x2, y2], [x1, y1, x2, y2]]
    temp_box: (2, 4)
    updated: (2, 4) boolean
    r_type: int (0-9)
    threshold: float
    """
    new_box = box.copy()
    constraint = [] # list of [box_idx_in_pair, side_idx]
    
    # Internal helpers mapping to Matlab logic
    # idx1, idx2 are (box_idx, side_idx) tuples. box_idx 0 or 1.
    # side_idx: 0:x1, 1:y1, 2:x2, 3:y2
    
    def align(idx1, idx2, thresh, attach=False):
        # idx1, idx2: tuples (box_i, coord_j)
        # Check condition
        b1_i, b1_j = idx1
        b2_i, b2_j = idx2
        
        diff = abs(temp_box[b1_i, b1_j] - temp_box[b2_i, b2_j])
        
        if diff <= thresh:
            updated1 = updated[b1_i, b1_j]
            updated2 = updated[b2_i, b2_j]
            
            val = 0.0
            
            if updated1 and not updated2:
                new_box[b2_i, b2_j] = new_box[b1_i, b1_j]
            elif updated2 and not updated1:
                new_box[b1_i, b1_j] = new_box[b2_i, b2_j]
            elif not updated1 and not updated2:
                if attach:
                    new_box[b2_i, b2_j] = new_box[b1_i, b1_j]
                else:
                    y = (new_box[b1_i, b1_j] + new_box[b2_i, b2_j]) / 2.0
                    new_box[b1_i, b1_j] = y
                    new_box[b2_i, b2_j] = y
                    
            # Handle constraints recording? 
            # Matlab: constraint(idx, :) = [idx1(2) idx2(2)]; or swapped
            # We will just return aligned pairs indices relative to the pair
            constraint.append([b1_i, b1_j, b2_i, b2_j]) # Basic record
            
    def alignV(is_left):
        # isLeft true: idx1=0 (x1/left), idx2=2 (x2/right) of other box?
        # Matlab: idx1=1 (x1), idx2=3 (x2 in matlab 1-based, 3 is x2)
        # Here: 0 is x1, 2 is x2.
        if is_left:
            idx1_side = 0
            idx2_side = 2
        else:
            idx1_side = 2
            idx2_side = 0
            
        # if abs(tempBox(2,idx1) - tempBox(1,idx2)) <= abs(tempBox(2,idx2) - tempBox(1,idx2))
        # Checks tempBox[1, idx1_side] vs tempBox[0, idx2_side] etc?
        # Matlab: tempBox(2,idx1) -> box 2, side idx1.
        
        # Mapping:
        # Matlab box index 1 -> Python 0
        # Matlab box index 2 -> Python 1
        
        d1 = abs(temp_box[1, idx1_side] - temp_box[0, idx2_side])
        d2 = abs(temp_box[1, idx2_side] - temp_box[0, idx2_side])
        
        if d1 <= d2:
            align((1, idx1_side), (0, idx2_side), threshold/2)
        else:
            align((1, idx2_side), (0, idx2_side), threshold/2)

    def alignH(is_above):
        # isAbove true: idx1=2 (y1/top), idx2=4 (y2/bottom)?
        # Matlab side indices: 1:x1, 2:y1, 3:x2, 4:y2
        # Python: 0:x1, 1:y1, 2:x2, 3:y2
        if is_above:
            idx1_side = 1
            idx2_side = 3
        else:
            idx1_side = 3
            idx2_side = 1
            
        d1 = abs(temp_box[1, idx1_side] - temp_box[0, idx2_side])
        d2 = abs(temp_box[1, idx2_side] - temp_box[0, idx2_side])
        
        if d1 <= d2:
            align((1, idx1_side), (0, idx2_side), threshold/2)
        else:
            align((1, idx2_side), (0, idx2_side), threshold/2)


    # Type mappings
    # 0 left-above, 1 left-below, 2 left-of, 3 above, 4 inside, 5 surrounding
    # 6 below, 7 right-of, 8 right-above, 9 right-below
    
    # Python indices for sides: x1:0, y1:1, x2:2, y2:3
    # Matlab arguments: align([box_idx, side_idx], ...) 
    # Matlab box indices are 2 and 1 mostly.
    
    if r_type == 0:
        alignV(True)
        alignH(True)
    elif r_type == 1:
        alignV(True)
        alignH(False)
    elif r_type == 2:
        # align([2,1], [1,3], threshold); -> box1 x1, box0 x2
        align((1, 0), (0, 2), threshold)
        align((1, 1), (0, 1), threshold/2)
        align((1, 3), (0, 3), threshold/2)
    elif r_type == 3:
        # align([2,2], [1,4], threshold); -> box1 y1, box0 y2
        align((1, 1), (0, 3), threshold)
        align((1, 0), (0, 0), threshold/2)
        align((1, 2), (0, 2), threshold/2)
    elif r_type == 4: # inside
        align((1, 0), (0, 0), threshold, True)
        align((1, 1), (0, 1), threshold, True)
        align((1, 2), (0, 2), threshold, True)
        align((1, 3), (0, 3), threshold, True)
    elif r_type == 5: # surrounding
        align((0, 0), (1, 0), threshold, True)
        align((0, 1), (1, 1), threshold, True)
        align((0, 2), (1, 2), threshold, True)
        align((0, 3), (1, 3), threshold, True)
    elif r_type == 6: # below
        align((1, 3), (0, 1), threshold)
        align((1, 0), (0, 0), threshold/2)
        align((1, 2), (0, 2), threshold/2)
    elif r_type == 7: # right-of
        align((1, 2), (0, 0), threshold)
        align((1, 1), (0, 1), threshold/2)
        align((1, 3), (0, 3), threshold/2)
    elif r_type == 8:
        alignV(False)
        alignH(True)
    elif r_type == 9:
        alignV(False)
        alignH(False)
        
    return new_box, constraint

def get_updated_count(updated, r_edge):
    # updated: (N, 4) boolean
    # r_edge: (M, 3) [u, v, type]
    count = np.zeros(len(r_edge))
    for k in range(len(r_edge)):
        u = int(r_edge[k, 0])
        v = int(r_edge[k, 1])
        # sum of updated flags for both boxes
        count[k] = np.sum(updated[u]) + np.sum(updated[v])
    return count

def align_neighbor(box, r_edge, updated, threshold):
    """
    box: (N, 4)
    r_edge: (M, 3)
    updated: (N, 4) boolean
    threshold: float
    """
    box = np.array(box, dtype=float)
    temp_box = box.copy()
    
    if updated is None:
        updated = np.zeros(box.shape, dtype=bool)
    else:
        updated = updated.copy() # Avoid modifying original if needed, but logic updates inplace?
        
    constraint = []
    
    n_edges = len(r_edge)
    checked = np.zeros(n_edges, dtype=bool)
    
    updated_count = get_updated_count(updated, r_edge)
    
    for _ in range(n_edges):
        # find max updated count among unchecked
        unchecked_indices = np.where(~checked)[0]
        if len(unchecked_indices) == 0:
            break
            
        # maxk(..., 1) -> argmax
        # In case of ties, Matlab behavior might be specific, but argmax is fine
        sub_counts = updated_count[unchecked_indices]
        max_idx_sub = np.argmax(sub_counts)
        t = unchecked_indices[max_idx_sub]
        
        checked[t] = True
        
        u = int(r_edge[t, 0])
        v = int(r_edge[t, 1])
        r_type = int(r_edge[t, 2])
        
        idx = [u, v]
        
        # Call align_adjacent_room3
        # Pass slice of box, temp_box, updated corresponding to u, v
        sub_box = box[idx]
        sub_temp = temp_box[idx]
        sub_updated = updated[idx]
        
        b_aligned, c_list = align_adjacent_room3(sub_box, sub_temp, sub_updated, r_type, threshold)
        
        # Update box
        box[idx] = b_aligned
        
        # Update updated and process constraints
        for k in range(len(idx)):
            # c_list logic: it returned list of [box_idx_in_pair, side_idx, ...]
            # We need to update user 'updated' array
            # And map relative box indices back to global u, v
            pass
            
        # Since I didn't return detailed updated map from align_adjacent, I need to infer or adjust logic
        # Re-implementing update logic inline with return:
        
        # Iterate over changes to set updated flags
        # Also need to handle b(j, 1) == b(j, 3) checks from Matlab
        
        # Let's inspect differences to set updated
        for k in range(2):
            global_idx = idx[k]
            for side in range(4):
                if sub_box[k, side] != b_aligned[k, side]: # Changed
                    # In Matlab: updated(idx(j), c(:,j)) = true;
                    # But align_adjacent_room3 calculates based on updated logic inside
                    pass
        
        # Actually standardizing the update:
        # If value changed, it is 'updated'.
        # Or if it was assigned from an updated value.
        # Let's trust the 'updated' propagation logic in align_adjacent_room3 if reimplemented correctly.
        # But align_adjacent_room3 uses local copies.
        
        # Refined alignment logic to match propagation:
        # In my python align(), I modified new_box. 
        # I need to reflect 'updated' status back to main loop.
        
        # Re-run logic to verify specific updates if needed but simpler:
        updated[idx] = sub_updated # This is wrong, sub_updated wasn't modified in place by align() wrapper?
        
        # Correct approach: align() modified new_box based on updated. 
        # But we need to update 'updated' flags for next iterations!
        # "updated(idx(j), c(:,j)) = true;"
        # We need to know WHICH coordinates were updated in align().
        
        # Let's assume strict diff check:
        # If coordinate changed value OR was explicitly aligned (even if value same? No, usage implies propagation)
        
        # The Matlab code is explicit about which sides get updated.
        # "updated(idx(j), c(:,j)) = true;"
        # And "constraint" stores the indices.
        
        for constr in c_list:
            # constr: [local_box_idx, side_idx, ...]
            l_idx, side = constr[0], constr[1]
            g_idx = idx[l_idx]
            updated[g_idx, side] = True
            
            # Constraint for output
            # c(:, j) = (c(:,j)-1)*size(box,1) + double(idx(j)); -> Matlabs linear index logic
            # We will generate [g_idx, side]
            constraint.append([g_idx, side])
            
        # Width/Height zero check (b(j, 1) == b(j, 3))
        for k in range(2):
            g_idx = idx[k]
            # Width 0
            if box[g_idx, 0] == box[g_idx, 2]:
                # restore original x
                box[g_idx, [0, 2]] = temp_box[g_idx, [0, 2]]
                updated[g_idx, [0, 2]] = False
            # Height 0
            if box[g_idx, 1] == box[g_idx, 3]:
                box[g_idx, [1, 3]] = temp_box[g_idx, [1, 3]]
                updated[g_idx, [1, 3]] = False
                
        # Update updatedCount
        updated_count = get_updated_count(updated, r_edge)
        
    return constraint, box, updated
