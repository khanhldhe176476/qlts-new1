# HƯỚNG DẪN SỬ DỤNG TÍNH NĂNG BẢO HÀNH

## Các tính năng mới đã thêm

### 1. Thông tin người liên hệ bảo hành
- **Tên người liên hệ**: Tên người phụ trách bảo hành
- **Số điện thoại**: SĐT liên hệ
- **Email**: Email liên hệ
- **Website/Link**: Link website bảo hành

### 2. Upload hóa đơn/phiếu giao hàng
- Upload file hóa đơn hoặc phiếu giao hàng khi mua bán
- Định dạng hỗ trợ: PDF, PNG, JPG, JPEG, GIF, DOC, DOCX, XLS, XLSX
- Tối đa 10MB
- File được lưu tại: `instance/uploads/`

### 3. Thời gian bảo hành
- **Ngày bắt đầu bảo hành**: Ngày bắt đầu
- **Thời gian bảo hành (tháng)**: Số tháng bảo hành
- **Ngày kết thúc**: Tự động tính từ ngày bắt đầu + số tháng
- Hiển thị trạng thái:
  - ✅ **Đang bảo hành**: Màu xanh, hiển thị ngày bắt đầu - kết thúc
  - ⚠️ **Sắp hết hạn**: Màu vàng
  - ❌ **Hết hạn**: Màu đỏ
  - ➖ **Không có bảo hành**: Hiển thị "Không có"

## Cách sử dụng

### Bước 1: Chạy Migration
Trước khi sử dụng, cần chạy migration để thêm các cột mới vào database:

```bash
py migrate_add_warranty_fields.py
```

### Bước 2: Thêm/Sửa tài sản
1. Vào **Tài sản** > **Thêm mới** hoặc **Chỉnh sửa**
2. Cuộn xuống phần **Thông tin bảo hành**
3. Điền thông tin:
   - Ngày bắt đầu bảo hành
   - Thời gian bảo hành (tháng) - ngày kết thúc sẽ tự động tính
   - Tên, SĐT, Email, Website người liên hệ
4. Upload hóa đơn/phiếu giao hàng (nếu có)
5. Lưu

### Bước 3: Xem thông tin bảo hành
- Trong danh sách tài sản, cột **Bảo hành** hiển thị:
  - Ngày bắt đầu - Ngày kết thúc (nếu có)
  - Badge màu theo trạng thái
  - "Không có" nếu không có bảo hành
- Cột **Hóa đơn** có nút download nếu đã upload

## Lưu ý

1. **Migration**: Chỉ cần chạy một lần khi cài đặt tính năng mới
2. **File upload**: File được lưu với tên unique để tránh trùng lặp
3. **Thời gian bảo hành**: Tính xấp xỉ 30 ngày/tháng
4. **Xóa file**: Khi xóa tài sản, file hóa đơn vẫn còn trong thư mục uploads (có thể dọn dẹp thủ công)

## Cấu hình

Có thể thay đổi trong file `.env`:
```
UPLOAD_FOLDER=instance/uploads
MAX_UPLOAD_SIZE=10485760  # 10MB
```

