import pandas as pd
import re
import os
from google import genai
from google.genai import types

def fetch_shinsatech_data(sheet_url: str) -> str:
    """
    Fetch quy trình của Team Shinsatech.
    QC Note: Tái sử dụng logic Regex để auto-convert URL thành định dạng Export CSV.
    """
    try:
        csv_export_url = re.sub(r'/edit.*', '/export?format=csv', sheet_url)
        csv_export_url = csv_export_url.replace('#gid=', '&gid=')
        
        df = pd.read_csv(csv_export_url)
        df.dropna(how='all', inplace=True)
        
        context_text = "TÀI LIỆU QUY TRÌNH LÀM VIỆC - TEAM SHINSATECH:\n\n"
        context_text += df.to_string(index=False)
        return context_text
        
    except Exception as e:
        return f"Error Fetching Shinsatech Data: {str(e)}"

def get_shinsatech_chat_session(api_key: str, context: str):
    """
    Khởi tạo phiên Chat (Multi-turn) độc lập cho team Shinsatech.
    Tránh Garbage Collection bằng cách return cả Tuple (client, session).
    """
    client = genai.Client(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    
    system_prompt = f"""
    Bạn là Shinsa, trợ lý ảo của team Shinsatech.
    Dưới đây là cơ sở dữ liệu quy trình làm việc (Knowledge Base) hiện tại của team:
    {context}
    
    QUY TẮC PHẢN HỒI BẮT BUỘC (STRICT RULES):
    1. DỰA HOÀN TOÀN VÀO DỮ LIỆU: Chỉ sử dụng thông tin được cung cấp trong Knowledge Base bên trên để trả lời. Trả lời ngắn gọn, đúng trọng tâm.
    2. SUY LUẬN LOGIC (NEGATIVE CASES): Nếu dữ liệu CÓ ĐỀ CẬP đến một danh sách cụ thể, và user hỏi về một đối tượng nằm ngoài danh sách đó, hãy trả lời rõ ràng.
    3. XỬ LÝ DỮ LIỆU TRỐNG (OUT OF SCOPE): Nếu người dùng hỏi về vấn đề HOÀN TOÀN KHÔNG XUẤT HIỆN trong Knowledge Base, BẮT BUỘC trả lời: "Thông tin này Shinsa chưa được cập nhật, bạn vui lòng liên hệ người quản lý".
    4. PRESERVE EXACT FORMAT: Khi yêu cầu Template, BẮT BUỘC xuất RAW text bằng Markdown Code Block (```text ... ```), giữ nguyên mọi khoảng trắng và ngắt dòng.
    """
    
    chat_session = client.chats.create(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2, 
        )
    )
    return client, chat_session
