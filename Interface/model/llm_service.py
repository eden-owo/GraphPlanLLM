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
    "BedRoom",       # 廚房
    "Bathroom",      # 浴室
    "Kitchen",       # 廚房
    "Balcony",       # 陽台
    "Storage",       # 儲藏室
]

SYSTEM_PROMPT = """你是一個格局規劃助手。根據用戶的需求描述，輸出 JSON 格式的房間配置。

可用的房間類型:
- BedRoom (臥室)
- Kitchen (廚房)
- Bathroom (浴室)
- Balcony (陽台)
- Storage (儲藏室)

輸出格式 (純 JSON，不要 markdown):
{
  "nodes": ["房間類型1", "房間類型2", ...],
  "edges": [[節點A索引, 節點B索引], ...]
}

規則:
1. 浴室通常連接臥室或客廳
2. 廚房通常連接客廳或餐廳
3. 陽台通常連接臥室或客廳
4. 所有房間應該形成連通圖（互相可達）
5. 如果用戶說「三房」，表示需要3間臥室類型的房間
6. edges 中的數字是 nodes 數組的索引（從0開始）

範例:
用戶: "兩房一廳一衛" 
輸出:
{           
  "nodes": ["BedRoom", "BedRoom", "Kitchen", "Bathroom"],
  "edges": [[0, 1], [0, 2], [0, 3], [1, 3]]
}
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
