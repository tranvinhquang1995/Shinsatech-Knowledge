import pandas as pd
import re
import os
from google import genai
from google.genai import types

def fetch_gamegate_data(sheet_url: str) -> str:
    """
    Fetch quy trình của Team GameGate. 
    QC Note: Đã bao gồm logic Regex catch mọi định dạng URL.
    """
    try:
        csv_export_url = re.sub(r'/edit.*', '/export?format=csv', sheet_url)
        csv_export_url = csv_export_url.replace('#gid=', '&gid=')
        
        df = pd.read_csv(csv_export_url)
        df.dropna(how='all', inplace=True)
        
        context_text = "TÀI LIỆU QUY TRÌNH LÀM VIỆC - TEAM GAMEGATE:\n\n"
        context_text += df.to_string(index=False)
        return context_text
        
    except Exception as e:
        return f"Error Fetching GameGate Data: {str(e)}"

def get_gamegate_chat_session(api_key: str, context: str):
    """
    Khởi tạo phiên Chat (Multi-turn) để dùng cho giao diện Streamlit.
    """
    client = genai.Client(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    
    system_prompt = f"""
        Bạn là Shinsa, trợ lý ảo của team GameGate.
        Bạn CHỈ ĐƯỢC PHÉP sử dụng thông tin trong phần [NGUỒN DỮ LIỆU GAMEGATE] dưới đây.
        
        [NGUỒN DỮ LIỆU GAMEGATE]:
        {context}
        
        RULE BẮT BUỘC:
        1. Phân tích ngữ nghĩa câu hỏi, đối chiếu với cột "Keywords" và "Standard Topic".
        2. Trả lời chi tiết dựa trên "Detailed Process" và "Exceptions" của TEAM GAMEGATE. Format bằng bullet points rõ ràng.
        3. Nếu câu hỏi của User chứa NHIỀU vấn đề khác nhau, hãy bóc tách và trả lời từng vấn đề một cách tuần tự dựa trên các hàng tương ứng trong [NGUỒN DỮ LIỆU GAMEGATE]. Sử dụng gạch đầu dòng rõ ràng cho từng vấn đề được giải quyết.
        4. SUY LUẬN LOGIC (NEGATIVE CASES): Nếu dữ liệu CÓ ĐỀ CẬP đến một danh sách hoặc quy định cụ thể (ví dụ: "danh sách cổng đang làm là 111, 112, 113"), và user hỏi về một đối tượng nằm ngoài danh sách đó (ví dụ: cổng 123), hãy trả lời rõ ràng dựa trên logic đó (ví dụ: "Theo dữ liệu hiện tại, team chỉ hỗ trợ các cổng 111, 112, 113, không bao gồm cổng 123").
        5. XỬ LÝ DỮ LIỆU TRỐNG (OUT OF SCOPE): Nếu người dùng hỏi về một vấn đề, từ khóa, hoặc quy trình HOÀN TOÀN KHÔNG XUẤT HIỆN trong Knowledge Base bên trên, BẠN KHÔNG ĐƯỢC SUY ĐOÁN. Bạn BẮT BUỘC phải trả lời chính xác từng chữ câu sau: "Thông tin này Shinsa chưa được cập nhật, bạn vui lòng liên hệ người quản lý".
        6. Đối với Module / Category là Template thì bạn BẮT BUỘC phải xuất TRỌN VẸN VÀ CHÍNH XÁC cấu trúc Markdown được định nghĩa trong dữ liệu ô Detailed Process, tuyệt đối không được tự ý lược bỏ, thay đổi vị trí xuống dòng, hay viết lại định dạng (format).
        """
    
    # Khởi tạo session chat để lưu lịch sử hỏi đáp
    chat_session = client.chats.create(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2, # Chốt requirement temperature 0.2
        )
    )
    return chat_session
