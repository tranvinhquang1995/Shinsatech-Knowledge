import pandas as pd
import google.generativeai as genai

def fetch_gamegate_data(sheet_url: str) -> str:
    """
    Fetch quy trình của Team GameGate. 
    Lưu ý: URL truyền vào phải trỏ đúng GID (Sheet ID) của tab GameGate.
    """
    try:
        csv_export_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv')
        csv_export_url = csv_export_url.replace('/edit', '/export?format=csv')
        
        df = pd.read_csv(csv_export_url)
        df.dropna(how='all', inplace=True)
        
        context_text = "TÀI LIỆU QUY TRÌNH LÀM VIỆC - TEAM GAMEGATE:\n\n"
        context_text += df.to_string(index=False)
        return context_text
    except Exception as e:
        return f"Error Fetching GameGate Data: {str(e)}"

def generate_gamegate_answer(api_key: str, context: str, user_question: str) -> str:
    # Khởi tạo model Gemini 3.6 Flash để tối ưu hóa việc phân tích quy trình
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    # ... (Giữ nguyên toàn bộ phần System Prompt và Exception handling cũ) ...
    
    system_prompt = f"""
    Bạn là một trợ lý ảo QA/QC chuyên trách hỗ trợ ĐỘC QUYỀN cho TEAM GAMEGATE (dự án Web/App Game Cocos).
    Bạn CHỈ ĐƯỢC PHÉP sử dụng thông tin trong phần [NGUỒN DỮ LIỆU GAMEGATE] dưới đây.
    
    [NGUỒN DỮ LIỆU GAMEGATE]:
    {context}
    
    RULE BẮT BUỘC:
    1. Phân tích ngữ nghĩa câu hỏi, đối chiếu với cột "Keywords" và "Standard Topic".
    2. Trả lời chi tiết dựa trên "Detailed Process" và "Exceptions" của TEAM GAMEGATE. Format bằng bullet points rõ ràng.
    3. Nếu câu hỏi KHÔNG THỂ match với bất kỳ data nào, TUYỆT ĐỐI KHÔNG SUY DIỄN. Bắt buộc trả lời đúng nguyên văn: "Thông tin này chưa được cập nhật, vui lòng liên hệ người quản lý".
    4. Nếu câu hỏi của User chứa NHIỀU vấn đề khác nhau, hãy bóc tách và trả lời từng vấn đề một cách tuần tự dựa trên các hàng tương ứng trong [NGUỒN DỮ LIỆU GAMEGATE]. Sử dụng gạch đầu dòng rõ ràng cho từng vấn đề được giải quyết.
    """
    
    try:
        response = model.generate_content(
            f"{system_prompt}\n\nCâu hỏi của User: {user_question}",
            generation_config=genai.types.GenerationConfig(temperature=0.1) 
        )
        return response.text
    except Exception as e:
        error_msg = str(e)
        # Catch riêng lỗi Rate Limit (429) để báo cho user
        if "429" in error_msg or "quota" in error_msg.lower():
            return "⚠️ Shinsa đang tiếp nhận quá nhiều câu hỏi cùng lúc (Quá tải). Bạn vui lòng chờ khoảng 1 phút rồi hỏi lại nhé!"
        # Catch các lỗi hệ thống khác
        return f"System Error: Đã xảy ra lỗi kết nối. Detail: {error_msg}"
