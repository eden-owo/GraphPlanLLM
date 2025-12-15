from  model.floorplan import *
from  model.box_utils import *
from  model.model import Model
import os
from  model.utils import *

import Houseweb.views as vw

import numpy as np
import time
import math
# import matlab.engine
  

global adjust,indxlist
adjust=False

def get_data(fp):
    batch = list(fp.get_test_data())
    batch[0] = batch[0].unsqueeze(0).cuda()
    batch[1] = batch[1].cuda()
    batch[2] = batch[2].cuda()
    batch[3] = batch[3].cuda()
    batch[4] = batch[4].cuda()
    return batch

def test(model,fp):
    with torch.no_grad():
        batch = get_data(fp)
        boundary,inside_box,rooms,attrs,triples = batch
        model_out = model(
            rooms, 
            triples, 
            boundary,
            obj_to_img = None,
            attributes = attrs,
            boxes_gt= None, 
            generate = True,
            refine = True,
            relative = True,
            inside_box=inside_box
        )
        boxes_pred,  gene_layout, boxes_refine= model_out
        boxes_pred = boxes_pred.detach()
        boxes_pred = centers_to_extents(boxes_pred)
        boxes_refine = boxes_refine.detach()
        boxes_refine = centers_to_extents(boxes_refine)
        gene_layout = gene_layout*boundary[:,:1]
        gene_preds = torch.argmax(gene_layout.softmax(1).detach(),dim=1)
        return boxes_pred.squeeze().cpu().numpy(),gene_preds.squeeze().cpu().double().numpy(),boxes_refine.squeeze().cpu().numpy()

def load_model():
    
    model = Model()
    model.cuda(0)
    model.load_state_dict(
        torch.load('./model/model.pth', map_location={'cuda:0': 'cuda:0'}))
    model.eval()
    return model

def get_userinfo(userRoomID,adptRoomID):
    start = time.perf_counter()
    global model
    test_index = vw.testNameList.index(userRoomID.split(".")[0])
    test_data = vw.test_data[test_index]

    # boundary
    Boundary = test_data.boundary
    boundary=[[float(x),float(y),float(z),float(k)] for x,y,z,k in list(Boundary)]
    
    test_fp =FloorPlan(test_data)

    train_index = vw.trainNameList.index(adptRoomID.split(".")[0])
    train_data = vw.train_data[train_index]
    train_fp =FloorPlan(train_data,train=True)
    fp_end = test_fp.adapt_graph(train_fp)
    fp_end.adjust_graph()
    return fp_end


def get_userinfo_adjust(userRoomID,adptRoomID,NewGraph):
    global adjust,indxlist
    test_index = vw.testNameList.index(userRoomID.split(".")[0])
    test_data = vw.test_data[test_index]
    # boundary
    Boundary = test_data.boundary
    boundary=[[float(x),float(y),float(z),float(k)] for x,y,z,k in list(Boundary)]
    
    test_fp =FloorPlan(test_data)

    train_index = vw.trainNameList.index(adptRoomID.split(".")[0])
    train_data = vw.train_data[train_index]
    train_fp =FloorPlan(train_data,train=True)
    fp_end = test_fp.adapt_graph(train_fp)
    fp_end.adjust_graph()

    
    newNode = NewGraph[0]
    newEdge = NewGraph[1]
    oldNode = NewGraph[2]
    
    temp = []
    for newindx, newrmname, newx, newy,scalesize in newNode:
        for type, oldrmname, oldx, oldy, oldindx in oldNode:
            if (int(newindx) == oldindx):
                tmp=int(newindx), (newx - oldx), ( newy- oldy),float(scalesize)
                temp.append(tmp)
    newbox=[]
    print(adjust)
    if adjust==True:
        oldbox = []
        for i in range(len(vw.boxes_pred)):
            indxtmp=[vw.boxes_pred[i][0],vw.boxes_pred[i][1],vw.boxes_pred[i][2],vw.boxes_pred[i][3],vw.boxes_pred[i][0]]
            oldbox.append(indxtmp)
    if adjust==False:
        indxlist=[]
        oldbox=fp_end.data.box.tolist()
        for i in range(len(oldbox)):
            indxlist.append([oldbox[i][4]])
        indxlist=np.array(indxlist)
        adjust=True
    oldbox=fp_end.data.box.tolist()

    # print("oldbox",oldbox)
    # print(oldbox,"oldbox")
    X=0
    Y=0
    for i in range(len(oldbox)):
        X= X+(oldbox[i][2]-oldbox[i][0])
        Y= Y+(oldbox[i][3]-oldbox[i][1])
    x_ave=(X/len(oldbox))/2
    y_ave=(Y/len(oldbox))/2

    index_mapping = {}
    #  The room that already exists
    #  Move: Just by the distance
    for newindx, tempx, tempy,scalesize in temp:
        index_mapping[newindx] = len(newbox)
        tmpbox=[]
        scalesize = int(scalesize)
        if scalesize<1:
            scale = math.sqrt(scalesize)
            scalex = (oldbox[newindx][2] - oldbox[newindx][0]) * (1 - scale) / 2
            scaley = (oldbox[newindx][3] - oldbox[newindx][1]) * (1 - scale) / 2
            tmpbox = [(oldbox[newindx][0] + tempx) + scalex, (oldbox[newindx][1] + tempy)+scaley,
                      (oldbox[newindx][2] + tempx) - scalex, (oldbox[newindx][3] + tempy) - scaley, oldbox[newindx][4]]
        if scalesize == 1:
            tmpbox = [(oldbox[newindx][0] + tempx) , (oldbox[newindx][1] + tempy) ,(oldbox[newindx][2] + tempx), (oldbox[newindx][3] + tempy), oldbox[newindx][4]]

        if scalesize>1:
            scale=math.sqrt(scalesize)
            scalex = (oldbox[newindx][2] - oldbox[newindx][0]) * ( scale-1) / 2
            scaley = (oldbox[newindx][3] - oldbox[newindx][1]) * (scale-1) / 2
            tmpbox = [(oldbox[newindx][0] + tempx) - scalex, (oldbox[newindx][1] + tempy) - scaley,
                      (oldbox[newindx][2] + tempx) + scalex, (oldbox[newindx][3] + tempy) + scaley, oldbox[newindx][4]]

           
        newbox.append(tmpbox)

    #  The room just added
    #  Move: The room node with the average size of the existing room
    for newindx, newrmname, newx, newy,scalesize in newNode:
        if int(newindx)>(len(oldbox)-1):
            scalesize=int(scalesize)
            index_mapping[int(newindx)] = (len(newbox))
            tmpbox=[]
            if scalesize < 1:
                scale = math.sqrt(scalesize)
                scalex = x_ave * (1 - scale) / 2
                scaley = y_ave* (1 - scale) / 2
                tmpbox = [(newx-x_ave) +scalex,(newy-y_ave) +scaley,(newx+x_ave)-scalex,(newy+y_ave)-scaley,vocab['object_name_to_idx'][newrmname]]

            if scalesize == 1:
                tmpbox = [(newx - x_ave), (newy - y_ave), (newx + x_ave), (newy + y_ave),vocab['object_name_to_idx'][newrmname]]
            if scalesize > 1:
                scale = math.sqrt(scalesize)
                scalex = x_ave * (scale - 1) / 2
                scaley = y_ave * (scale - 1) / 2
                tmpbox = [(newx-x_ave) - scalex, (newy-y_ave)  - scaley,(newx+x_ave) + scalex, (newy+y_ave) + scaley,vocab['object_name_to_idx'][newrmname]]
            print(scalesize)
            newbox.append(tmpbox)

    fp_end.data.box=np.array(newbox)
    adjust_Edge=[]
    for u, v in newEdge:
        tmp=[index_mapping[int(u)],index_mapping[int(v)], 0]
        adjust_Edge.append(tmp)
    fp_end.data.edge=np.array(adjust_Edge)
    rNode = fp_end.get_rooms(tensor=False)

    rEdge = fp_end.get_triples(tensor=False)[:, [0, 2, 1]]
    Edge = [[float(u), float(v), float(type2)] for u, v, type2 in rEdge]

    s=time.perf_counter()
    boxes_pred, gene_layout, boxes_refine = test(vw.model, fp_end)

    e=time.perf_counter()
    print(' model test time: %s Seconds' % (e - s))

    boxes_pred = boxes_pred * 255
    
    # fp_end.data.gene = gene_layout # Keep gene? Matlab logic passed gene as arg but python align_fp doesn't use it yet (check impl)
    # My python align_fp does not take gene arg. Original matlab align_fp signature:
    # function [newBox, order, rBoundary] = align_fp(boundary, rBox, rType, rEdge, fp, threshold, drawResult)
    # It takes 'fp' which seems to be gene_layout? 
    # In test.py: engview.align_fp(..., matlab.double(fp_end.data.gene...), ...)
    # But does align_fp.m use 'fp'? 
    # Viewing align_fp.m: "plot_fp(..., fp, ...)" if drawResult is true.
    # It is NOT used for alignment logic. So I can ignore it in Python implementation if I don't draw.
    
    fp_end.data.gene = gene_layout
    rBox = boxes_pred[:]
    # Box = [[float(x), float(y), float(z), float(k)] for x, y, z, k in rBox]
    
    # Direct Numpy usage
    Box = rBox
    
    fp_end.data.boundary = np.array(boundary)
    
    # rNode is tensor? get_rooms(tensor=False) returns np array usually
    fp_end.data.rType = np.array(rNode).astype(int)
    fp_end.data.refineBox = np.array(Box)
    fp_end.data.rEdge = np.array(Edge)
    
    startcom = time.perf_counter()
    # Call Python align_fp
    # align_fp(boundary, r_box, r_type, r_edge, fp=None, threshold=18.0, draw_result=False)
    from align_fp_python import align_fp
    
    box_out, box_order, rBoundary = align_fp(
        boundary, 
        Box, 
        rNode, 
        Edge, 
        fp=None, # gene_layout ignored 
        threshold=18.0
    )
    
    endcom = time.perf_counter()
    print(' python.compute time: %s Seconds' % (endcom - startcom))

    fp_end.data.newBox = np.array(box_out)
    fp_end.data.order = np.array(box_order)
    fp_end.data.rBoundary = [np.array(rb) for rb in rBoundary]
    return fp_end,box_out,box_order, gene_layout, boxes_refine


def get_userinfo_net(userRoomID,adptRoomID):
    global model
    test_index = vw.testNameList.index(userRoomID.split(".")[0])
    test_data = vw.test_data[test_index]

    # boundary
    Boundary = test_data.boundary
    boundary = [[float(x), float(y), float(z), float(k)] for x, y, z, k in list(Boundary)]
    test_fp = FloorPlan(test_data)

    train_index = vw.trainNameList.index(adptRoomID.split(".")[0])
    train_data = vw.train_data[train_index]
    train_fp = FloorPlan(train_data, train=True)
    fp_end = test_fp.adapt_graph(train_fp)
    fp_end.adjust_graph()
    boxes_pred, gene_layout, boxes_refeine = test(model, fp_end)
    boxes_pred=boxes_pred*255
    for i in range(len(boxes_pred)):
        for j in range(len(boxes_pred[i])):
            boxes_pred[i][j]=float(boxes_pred[i][j])
    return fp_end,boxes_pred, gene_layout, boxes_refeine


def get_llm_layout(testname, nodes, edges, positions):
    """
    使用 LLM 生成的 Graph 產生房間佈局
    
    Args:
        testname: 測試資料名稱 (用戶邊界)
        nodes: 房間類型列表 ["LivingRoom", "MasterRoom", ...]
        edges: 邊連接 [[0, 1], [1, 2], ...]
        positions: 節點位置 [[x, y], ...]
        
    Returns:
        dict: 包含 roomret, indoor, windows, windowsline 等資料
    """
    global model
    
    # 取得用戶邊界資料
    test_index = vw.testNameList.index(testname.split(".")[0])
    test_data = vw.test_data[test_index]
    
    # 創建一個簡單的資料結構來模擬 FloorPlan 需要的 data 物件
    class LLMGraphData:
        def __init__(self, boundary, box, edge):
            self.boundary = boundary
            self.box = box
            self.edge = edge
            self.order = None
    
    # 準備邊界資料
    boundary = test_data.boundary
    
    # 計算邊界的 bounding box
    external = boundary[:, :2]
    x_min, x_max = np.min(external[:, 0]), np.max(external[:, 0])
    y_min, y_max = np.min(external[:, 1]), np.max(external[:, 1])
    
    # 根據 positions 和 nodes 創建初始 box
    # box 格式: [x1, y1, x2, y2, type_id]
    boxes = []
    avg_width = (x_max - x_min) / (len(nodes) ** 0.5 + 1)
    avg_height = (y_max - y_min) / (len(nodes) ** 0.5 + 1)
    
    for i, node_type in enumerate(nodes):
        type_id = vocab['object_name_to_idx'].get(node_type, 0)
        x, y = positions[i]
        
        # 計算初始房間大小
        half_w = avg_width / 2
        half_h = avg_height / 2
        
        x1 = max(x - half_w, x_min + 5)
        y1 = max(y - half_h, y_min + 5)
        x2 = min(x + half_w, x_max - 5)
        y2 = min(y + half_h, y_max - 5)
        
        boxes.append([x1, y1, x2, y2, type_id])
    
    boxes = np.array(boxes)
    
    # 創建 edge 資料
    edge_array = np.array([[e[0], e[1], 0] for e in edges])
    
    # 創建 LLM Graph Data
    llm_data = LLMGraphData(boundary, boxes, edge_array)
    
    # 使用 FloorPlan 封裝
    fp = FloorPlan(llm_data)
    fp.adjust_graph()  # 調整節點位置
    
    # 呼叫模型生成佈局
    s = time.perf_counter()
    boxes_pred, gene_layout, boxes_refine = test(vw.model, fp)
    e = time.perf_counter()
    print(f' LLM model test time: {e - s:.2f}s')
    
    boxes_pred = boxes_pred * 255
    
    # 準備 align_fp 需要的資料
    boundary_list = [[float(b[0]), float(b[1]), float(b[2]) if len(b) > 2 else 0, float(b[3]) if len(b) > 3 else 0] 
                     for b in boundary.tolist()]
    
    rooms = fp.get_rooms(tensor=False)
    rNode = np.array(rooms).astype(int)
    
    # 準備 Edge 資料 (從 triples 轉換)
    triples = fp.get_triples(tensor=False)
    Edge = [[float(u), float(v), float(t)] for u, v, t in triples[:, [0, 2, 1]]]
    
    # 呼叫 align_fp 進行佈局優化
    align_start = time.perf_counter()
    try:
        from align_fp_python import align_fp
        
        box_out, box_order, rBoundary = align_fp(
            boundary_list, 
            boxes_pred, 
            rNode, 
            Edge, 
            fp=None,
            threshold=18.0
        )
        
        align_end = time.perf_counter()
        print(f' LLM align_fp time: {align_end - align_start:.2f}s')
        
        # 使用 align_fp 優化後的結果
        boxes_final = np.array(box_out)
        box_order = list(box_order)
        
    except Exception as e:
        print(f' align_fp 錯誤 (使用原始預測): {e}')
        import traceback
        traceback.print_exc()
        # 如果 align_fp 失敗，使用原始預測
        boxes_final = boxes_pred
        box_order = list(range(1, len(nodes) + 1))
    
    # 組裝 roomret
    roomret = []
    for i in range(len(box_order)):
        idx = int(box_order[i]) - 1
        if idx < len(boxes_final):
            if hasattr(boxes_final[idx], 'tolist'):
                box = boxes_final[idx].tolist()
            else:
                box = list(boxes_final[idx])
            room_type = vocab['object_idx_to_name'][int(rooms[idx])] if idx < len(rooms) else nodes[idx]
            roomret.append([box, [room_type], idx])
    
    # 簡化的門窗資料
    indoor = []
    windows = []
    windowsline = []
    
    return {
        'roomret': roomret,
        'indoor': indoor,
        'windows': windows,
        'windowsline': windowsline,
        'boxes_pred': boxes_final.tolist() if hasattr(boxes_final, 'tolist') else list(boxes_final),
        'box_order': box_order
    }


if __name__ == "__main__":
    pass

