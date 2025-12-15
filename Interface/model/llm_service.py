"""
LLM Service Module
將自然語言轉換為格局圖 (nodes + edges)
"""
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 初始化 OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 可用的房間類型 (對應 utils.py 中的 room_label)
ROOM_TYPES = [
    "LivingRoom",    # 客廳
    "MasterRoom",    # 主臥室
    "SecondRoom",    # 次臥室
    "ChildRoom",     # 兒童房
    "StudyRoom",     # 書房
    "Kitchen",       # 廚房
    "Bathroom",      # 浴室
    "Balcony",       # 陽台
    "Storage",       # 儲藏室
    "DiningRoom",    # 餐廳
    "GuestRoom",     # 客房
    "Entrance",      # 玄關
]

SYSTEM_PROMPT = """你是一個格局規劃助手。根據用戶的需求描述，輸出 JSON 格式的房間配置。

可用的房間類型:
- LivingRoom (客廳) - 中心區域，通常連接其他房間
- MasterRoom (主臥室)
- SecondRoom (次臥室) 
- ChildRoom (兒童房)
- StudyRoom (書房)
- Kitchen (廚房)
- Bathroom (衛浴/浴室)
- Balcony (陽台)
- Storage (儲藏室)
- DiningRoom (餐廳)
- GuestRoom (客房)

輸出格式 (純 JSON，不要 markdown):
{
  "nodes": ["房間類型1", "房間類型2", ...],
  "edges": [[節點A索引, 節點B索引], ...]
}

重要規則:
1. 「客廳」必須是 LivingRoom，不是 Kitchen
2. 客廳(LivingRoom)是中心區域，應該連接到大多數其他房間
3. 浴室(Bathroom)通常連接到臥室或客廳
4. 廚房(Kitchen)通常連接客廳或餐廳
5. 陽台(Balcony)通常連接臥室或客廳
6. 「三房」= 3間臥室（可用 MasterRoom, SecondRoom, ChildRoom 等）
7. 「兩衛」= 2間浴室 (Bathroom)
8. edges 中的數字是 nodes 數組的索引（從0開始）
9. 所有房間必須形成連通圖（可互相到達）
10. 客廳應該是連接的中心點

範例1:
用戶: "兩房一廳一衛" 
輸出:
{           
  "nodes": ["LivingRoom", "MasterRoom", "SecondRoom", "Bathroom"],
  "edges": [[0, 1], [0, 2], [0, 3], [1, 3]]
}
說明: 客廳(0)連接所有房間，主臥(1)也連浴室(3)

範例2:
用戶: "三房兩衛一客廳"
輸出:
{
  "nodes": ["LivingRoom", "MasterRoom", "SecondRoom", "ChildRoom", "Bathroom", "Bathroom"],
  "edges": [[0, 1], [0, 2], [0, 3], [0, 4], [1, 4], [2, 5], [3, 5]]
}
說明: 客廳(0)連接所有臥室，主臥連浴室1，次臥和兒童房連浴室2
"""

def parse_natural_language(user_input: str) -> dict:
    """
    使用 LLM 將自然語言轉換為 nodes + edges
    
    Args:
        user_input: 用戶的自然語言描述，如 "三房兩衛一廳"
        
    Returns:
        dict: {"nodes": [...], "edges": [...]}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        # 嘗試解析 JSON
        # 處理可能的 markdown 格式 (```json ... ```)
        if content.startswith("```"):
            # 移除 markdown 代碼塊
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
        
        result = json.loads(content)
        
        # 驗證結果格式
        if "nodes" not in result or "edges" not in result:
            raise ValueError("LLM 回應缺少 nodes 或 edges")
        
        # 驗證房間類型
        for node in result["nodes"]:
            if node not in ROOM_TYPES:
                raise ValueError(f"未知的房間類型: {node}")
        
        # 驗證邊的索引
        num_nodes = len(result["nodes"])
        for edge in result["edges"]:
            if len(edge) != 2:
                raise ValueError(f"無效的邊格式: {edge}")
            if edge[0] >= num_nodes or edge[1] >= num_nodes:
                raise ValueError(f"邊的索引超出範圍: {edge}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON 解析錯誤: {e}")
        print(f"LLM 原始回應: {content}")
        raise ValueError(f"無法解析 LLM 回應為 JSON: {str(e)}")
    except Exception as e:
        print(f"LLM 服務錯誤: {e}")
        raise


if __name__ == "__main__":
    # 測試
    test_inputs = [
        "兩房一廳一衛",
        "三房兩衛一廳一廚",
        "主臥連陽台，還要一間書房和一間浴室"
    ]
    
    for inp in test_inputs:
        print(f"\n輸入: {inp}")
        try:
            result = parse_natural_language(inp)
            print(f"輸出: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"錯誤: {e}")
