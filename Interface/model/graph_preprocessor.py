"""
Graph Preprocessor Module
將簡化的 Graph (nodes + edges) 轉換為模型需要的完整格式
"""
import numpy as np
import math
from model.utils import vocab, room_label


# 房間的預設大小比例 (相對於邊界面積)
DEFAULT_ROOM_SIZES = {
    "LivingRoom": 0.20,
    "MasterRoom": 0.18,
    "Kitchen": 0.10,
    "Bathroom": 0.06,
    "DiningRoom": 0.12,
    "ChildRoom": 0.12,
    "StudyRoom": 0.10,
    "SecondRoom": 0.12,
    "GuestRoom": 0.12,
    "Balcony": 0.05,
    "Entrance": 0.04,
    "Storage": 0.04,
}


def force_directed_layout(nodes, edges, boundary, iterations=100):
    """
    使用力導向演算法計算節點的初始位置
    
    Args:
        nodes: 房間類型列表 ["LivingRoom", "MasterRoom", ...]
        edges: 邊連接 [[0, 1], [1, 2], ...]
        boundary: 邊界多邊形座標 [[x1,y1], [x2,y2], ...]
        iterations: 迭代次數
        
    Returns:
        positions: 每個節點的 (x, y) 座標
    """
    num_nodes = len(nodes)
    if num_nodes == 0:
        return []
    
    # 計算邊界的 bounding box
    boundary = np.array(boundary)
    if boundary.shape[1] >= 2:
        boundary = boundary[:, :2]  # 只取 x, y
    
    x_min, y_min = boundary.min(axis=0)
    x_max, y_max = boundary.max(axis=0)
    
    # 中心點
    cx, cy = (x_min + x_max) / 2, (y_min + y_max) / 2
    
    # 初始化位置: 在邊界中心附近隨機分布
    np.random.seed(42)  # 固定隨機種子以獲得一致結果
    positions = np.zeros((num_nodes, 2))
    
    # 使用更大的圓形分布作為初始位置 (充分利用邊界空間)
    radius = min(x_max - x_min, y_max - y_min) / 2.5  # 增大初始半徑
    for i in range(num_nodes):
        angle = 2 * math.pi * i / num_nodes
        positions[i] = [
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle)
        ]
    
    # 建立鄰接矩陣
    adj_matrix = np.zeros((num_nodes, num_nodes))
    for u, v in edges:
        adj_matrix[u][v] = 1
        adj_matrix[v][u] = 1
    
    # 力導向迭代
    k = radius / 1.5  # 增大理想距離
    
    for _ in range(iterations):
        forces = np.zeros((num_nodes, 2))
        
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i == j:
                    continue
                
                # 計算位移向量
                delta = positions[i] - positions[j]
                distance = max(np.linalg.norm(delta), 0.01)
                direction = delta / distance
                
                # 排斥力 (所有節點) - 增強排斥力
                repulsion = (k ** 2) / distance
                forces[i] += direction * repulsion * 0.3  # 增強排斥
                
                # 吸引力 (只有連接的節點) - 減弱吸引力
                if adj_matrix[i][j]:
                    attraction = (distance ** 2) / k
                    forces[i] -= direction * attraction * 0.02  # 減弱吸引
        
        # 邊界約束力
        for i in range(num_nodes):
            # 保持在邊界內
            margin = 20
            if positions[i][0] < x_min + margin:
                forces[i][0] += 5
            if positions[i][0] > x_max - margin:
                forces[i][0] -= 5
            if positions[i][1] < y_min + margin:
                forces[i][1] += 5
            if positions[i][1] > y_max - margin:
                forces[i][1] -= 5
        
        # 更新位置
        positions += forces * 0.1
        
        # 限制在邊界內
        positions[:, 0] = np.clip(positions[:, 0], x_min + 10, x_max - 10)
        positions[:, 1] = np.clip(positions[:, 1], y_min + 10, y_max - 10)
    
    return positions.tolist()


def infer_directions(positions, edges):
    """
    根據座標推斷節點之間的相對方向，生成 triples
    
    Args:
        positions: 節點座標 [[x, y], ...]
        edges: 邊連接 [[u, v], ...]
        
    Returns:
        triples: [[節點A, 關係類型, 節點B], ...]
    """
    triples = []
    positions = np.array(positions)
    
    for u, v in edges:
        ux, uy = positions[u]
        vx, vy = positions[v]
        
        dx = vx - ux
        dy = vy - uy
        
        # 根據相對位置判斷關係
        # 關係類型對應 vocab['pred_name_to_idx']
        if abs(dx) > abs(dy):
            if dx > 0:
                relation = 'right-of'  # v 在 u 的右邊
            else:
                relation = 'left-of'   # v 在 u 的左邊
        else:
            if dy > 0:
                relation = 'below'     # v 在 u 的下方
            else:
                relation = 'above'     # v 在 u 的上方
        
        rel_idx = vocab['pred_name_to_idx'].get(relation, 0)
        triples.append([int(u), rel_idx, int(v)])
    
    return triples


def calculate_room_sizes(nodes, boundary):
    """
    計算每個房間的大小 (用於節點繪製半徑)
    
    Args:
        nodes: 房間類型列表
        boundary: 邊界多邊形
        
    Returns:
        sizes: 每個房間的大小值列表
    """
    # 計算邊界面積
    boundary = np.array(boundary)
    if boundary.shape[1] >= 2:
        boundary = boundary[:, :2]
    
    x_min, y_min = boundary.min(axis=0)
    x_max, y_max = boundary.max(axis=0)
    
    # 使用固定的節點大小，讓節點更明顯
    base_size = 8  # 基礎大小
    
    sizes = []
    for node_type in nodes:
        ratio = DEFAULT_ROOM_SIZES.get(node_type, 0.1)
        # 根據房間比例調整大小
        size = base_size * (0.8 + ratio * 2)  # 範圍約 8~12
        sizes.append(max(size, 6))  # 最小值 6
    
    return sizes


def generate_graph_attributes(nodes, edges, boundary):
    """
    生成模型需要的完整 Graph 屬性
    
    Args:
        nodes: 房間類型列表 ["LivingRoom", "MasterRoom", ...]
        edges: 邊連接 [[0, 1], [1, 2], ...]
        boundary: 邊界多邊形座標 (從 test_data.boundary 取得)
        
    Returns:
        dict: {
            "rmpos": [[類型ID, 類型名稱, x, y, 索引], ...],
            "hsedge": [[u, v], ...],
            "rmsize": [[大小], ...],
            "triples": [[u, 關係, v], ...]
        }
    """
    # 轉換為 numpy array 便於處理
    boundary = np.array(boundary)
    if boundary.shape[1] > 2:
        boundary_2d = boundary[:, :2]
    else:
        boundary_2d = boundary
    
    # 1. 計算初始位置
    positions = force_directed_layout(nodes, edges, boundary_2d.tolist())
    
    # 2. 推斷相對方向
    triples = infer_directions(positions, edges)
    
    # 3. 計算房間大小
    sizes = calculate_room_sizes(nodes, boundary_2d.tolist())
    
    # 4. 組裝 rmpos
    rmpos = []
    for i, node_type in enumerate(nodes):
        type_id = vocab['object_name_to_idx'].get(node_type, 0)
        x, y = positions[i]
        rmpos.append([float(type_id), node_type, float(x), float(y), float(i)])
    
    # 5. 組裝 rmsize
    rmsize = [[size, nodes[i]] for i, size in enumerate(sizes)]
    
    # 6. 組裝 hsedge
    hsedge = [[int(u), int(v)] for u, v in edges]
    
    return {
        "rmpos": rmpos,
        "hsedge": hsedge,
        "rmsize": rmsize,
        "triples": triples,
        "nodes": nodes,
        "positions": positions
    }


if __name__ == "__main__":
    # 測試
    test_nodes = ["LivingRoom", "MasterRoom", "SecondRoom", "Bathroom", "Kitchen"]
    test_edges = [[0, 1], [0, 2], [0, 3], [0, 4], [1, 3]]
    test_boundary = [[0, 0], [256, 0], [256, 256], [0, 256]]
    
    result = generate_graph_attributes(test_nodes, test_edges, test_boundary)
    
    print("rmpos:", result["rmpos"])
    print("hsedge:", result["hsedge"])
    print("rmsize:", result["rmsize"])
    print("triples:", result["triples"])
