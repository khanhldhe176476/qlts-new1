from flask import Blueprint, jsonify

inventory_bp = Blueprint('inventory_bp', __name__, url_prefix='/api/inventory')


@inventory_bp.route('/business-doc', methods=['GET'])
def get_inventory_business_doc():
  """
  API trả về nội dung tài liệu nghiệp vụ kiểm kê (tĩnh).
  Có thể dùng cho frontend (React) hoặc các client khác.
  """
  return jsonify({
    "title": "Tài liệu nghiệp vụ - Kiểm kê tài sản",
    "sections": [
      {
        "key": "objectives",
        "title": "Mục tiêu kiểm kê",
        "items": [
          "Xác nhận thực tế từng tài sản do phường quản lý.",
          "Đối chiếu với sổ/phần mềm để phát hiện thừa, thiếu, hư hỏng, sai thông tin.",
          "Là căn cứ pháp lý cho: chốt sổ năm, tính hao mòn, ghi tăng/giảm, thanh lý hoặc điều chuyển."
        ]
      },
      {
        "key": "principles",
        "title": "Nguyên tắc kiểm kê",
        "items": [
          "Kiểm kê theo đúng thời điểm chốt kiểm kê.",
          "Mọi chênh lệch phải ghi rõ: nguyên nhân – hướng xử lý – thẩm quyền phê duyệt.",
          "Tài sản hỏng nặng chỉ ghi giảm khi có Quyết định thanh lý."
        ]
      }
    ]
  })

















