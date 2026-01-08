
from flask import request, jsonify, session, current_app

def ai_chat():
    """
    Giả lập AI Chatbot để hỗ trợ người dùng.
    Trong thực tế, bạn có thể thay thế logic này bằng cách gọi API OpenAI/Gemini/Anthropic.
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip().lower()
        
        if not user_message:
            return jsonify({'response': 'Tôi có thể giúp gì cho bạn?'})
            
        # Logic trả lời đơn giản dựa trên từ khóa (Rule-based)
        # Đây là nơi bạn có thể tích hợp LLM thực sự
        
        response = ""
        
        # 1. Chào hỏi
        if any(w in user_message for w in ['xin chào', 'hello', 'hi', 'chào']):
             response = f"Xin chào {session.get('username', 'bạn')}! Tôi là trợ lý ảo hỗ trợ quản lý tài sản. Tôi có thể giúp gì cho bạn?"
             
        # 2. Hỏi về cách thêm tài sản
        elif any(w in user_message for w in ['thêm tài sản', 'tạo tài sản', 'nhập tài sản', 'add asset']):
            response = """Để thêm tài sản mới, bạn hãy thực hiện theo các bước sau:
1. Nhấn vào menu <b>"Quản lý tài sản"</b> > <b>"Danh sách tài sản"</b>.
2. Nhấn nút <b>"Thêm mới"</b> (màu xanh lá) ở góc trên bên phải.
3. Điền đầy đủ thông tin (Tên, Loại, Giá, ...) và nhấn <b>"Lưu"</b>.
<br>Hoặc dùng nút <b>"Thêm nhanh"</b> ngay tại Dashboard."""

        # 3. Hỏi về bảo trì
        elif any(w in user_message for w in ['bảo trì', 'sửa chữa', 'hỏng', 'maintenance']):
            response = """Để quản lý bảo trì thiết bị:
1. Truy cập menu <b>"Bảo trì & Bàn giao"</b> > <b>"Bảo trì thiết bị"</b>.
2. Tại đây bạn có thể tạo lịch bảo trì mới hoặc cập nhật trạng thái các đơn bảo trì hiện có.
3. Hệ thống sẽ tự động nhắc nhở khi đến hạn bảo trì."""
            
        # 4. Hỏi về bàn giao/điều chuyển
        elif any(w in user_message for w in ['bàn giao', 'điều chuyển', 'giao tài sản', 'transfer']):
            response = """Để bàn giao tài sản cho nhân viên khác:
1. Vào menu <b>"Bảo trì & Bàn giao"</b> > <b>"Bàn giao tài sản"</b>.
2. Tạo phiếu bàn giao mới, chọn tài sản và người nhận.
3. Người nhận sẽ cần xác nhận trên hệ thống để hoàn tất quy trình."""

        # 5. Hỏi về báo cáo
        elif any(w in user_message for w in ['báo cáo', 'thống kê', 'in báo cáo', 'report']):
            response = """Hệ thống cung cấp nhiều loại báo cáo:
- <b>Tổng hợp tài sản</b>: Thống kê số lượng, giá trị theo loại.
- <b>Báo cáo khấu hao</b>: Theo dõi hao mòn tài sản.
- <b>Lịch sử bảo trì</b>: Xem chi tiết các lần sửa chữa.
<br>Vui lòng truy cập menu <b>"Báo cáo & Hệ thống"</b> > <b>"Báo cáo"</b> để xem chi tiết."""
            
        # 6. Hỏi về đổi mật khẩu/thông tin cá nhân
        elif any(w in user_message for w in ['mật khẩu', 'pass', 'thông tin cá nhân', 'profile']):
            current_user = session.get('username')
            response = f"""Để quản lý thông tin cá nhân của <b>{current_user}</b>:
1. Nhấn vào tên của bạn ở góc trên bên phải màn hình.
2. Chọn <b>"Thông tin cá nhân"</b> để xem hoặc <b>"Cài đặt"</b> để đổi mật khẩu.
3. Nhớ lưu lại thay đổi sau khi chỉnh sửa."""
            
        # 7. Mặc định
        else:
            response = """Xin lỗi, tôi chưa hiểu rõ câu hỏi của bạn. 
Bạn có thể thử hỏi về các chủ đề như: 
- <i>"Cách thêm tài sản mới"</i>
- <i>"Quy trình bảo trì thiết bị"</i>
- <i>"Xem báo cáo thống kê"</i>
- <i>"Cách bàn giao tài sản"</i>"""

        return jsonify({'response': response})
        
    except Exception as e:
        current_app.logger.error(f"AI Chat Error: {str(e)}")
        return jsonify({'response': 'Xin lỗi, hệ thống đang gặp sự cố. Vui lòng thử lại sau.'}), 500
