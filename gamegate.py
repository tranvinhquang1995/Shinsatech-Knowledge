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
    # model = genai.GenerativeModel('gemini-3.6-flash')
    model = genai.GenerativeModel('gemini-flash-lite-latest')
    
    # ... (Giữ nguyên toàn bộ phần System Prompt và Exception handling cũ) ...
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
    
    #Prompt dự phòng
    '''
    system_prompt = f"""
    Bạn là Shinsa, trợ lý ảo của team GameGate.
    Bạn CHỈ ĐƯỢC PHÉP sử dụng thông tin trong phần [NGUỒN DỮ LIỆU GAMEGATE] dưới đây.
    
    [NGUỒN DỮ LIỆU GAMEGATE]:
    {context}
    
    QUY TẮC PHẢN HỒI BẮT BUỘC (STRICT RULES):
    1. DỰA HOÀN TOÀN VÀO DỮ LIỆU: Chỉ sử dụng thông tin được cung cấp trong Knowledge Base bên trên để trả lời. Trả lời ngắn gọn, đúng trọng tâm.
    2. SUY LUẬN LOGIC (NEGATIVE CASES): Nếu dữ liệu CÓ ĐỀ CẬP đến một danh sách hoặc quy định cụ thể (ví dụ: "danh sách cổng đang làm là 111, 112, 113"), và user hỏi về một đối tượng nằm ngoài danh sách đó (ví dụ: cổng 123), hãy trả lời rõ ràng dựa trên logic đó (ví dụ: "Theo dữ liệu hiện tại, team chỉ hỗ trợ các cổng 111, 112, 113, không bao gồm cổng 123").
    3. XỬ LÝ DỮ LIỆU TRỐNG (OUT OF SCOPE): Nếu người dùng hỏi về một vấn đề, từ khóa, hoặc quy trình HOÀN TOÀN KHÔNG XUẤT HIỆN trong Knowledge Base bên trên, BẠN KHÔNG ĐƯỢC SUY ĐOÁN. Bạn BẮT BUỘC phải trả lời chính xác từng chữ câu sau: "Thông tin này Shinsa chưa được cập nhật, bạn vui lòng liên hệ người quản lý".
    """
    '''
    
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
