# Hướng Dẫn Setup Dự Án Sau Khi Clone Từ GitHub

## Vấn đề

Khi clone code từ GitHub về, bạn sẽ không có:
- Database file (instance/app.db)
- Dữ liệu mẫu trong database
- Các bảng database chưa được tạo

## Giải pháp

### Bước 1: Cài đặt thư viện

```bash
py -m pip install -r requirements.txt
```

### Bước 2: Khởi tạo Database và Dữ liệu

Có 2 cách:

#### Cách 1: Chạy ứng dụng (Tự động tạo database và admin user)

```bash
py run.py
```

Ứng dụng sẽ tự động:
- Tạo database nếu chưa có
- Tạo các bảng
- Tạo admin user mặc định:
  - Username: `admin`
  - Password: `admin123`

#### Cách 2: Chạy script khởi tạo dữ liệu mẫu

```bash
py init_new_data.py
```

Script này sẽ:
- Tạo tất cả các bảng
- Tạo roles (admin, manager, user)
- Tạo users mẫu
- Tạo asset types mẫu
- Tạo assets mẫu
- Tạo maintenance records mẫu

### Bước 3: Kiểm tra

1. Chạy ứng dụng:
```bash
py run.py
```

2. Truy cập: http://localhost:5000/

3. Đăng nhập với:
   - Username: `admin`
   - Password: `admin123`

## Cấu trúc Database

Sau khi khởi tạo, database sẽ có các bảng:
- `role` - Vai trò người dùng
- `user` - Người dùng
- `asset_type` - Loại tài sản
- `asset` - Tài sản
- `maintenance_record` - Bản ghi bảo trì
- `asset_transfer` - Bàn giao tài sản
- `audit_log` - Lịch sử thay đổi

## Lưu ý

1. **Database file** (`instance/app.db`) không được commit lên GitHub (đã thêm vào .gitignore)
2. Mỗi developer cần chạy script init để tạo database riêng
3. Dữ liệu mẫu chỉ để test, không phải dữ liệu thật
4. Nếu muốn reset database, xóa file `instance/app.db` và chạy lại `init_new_data.py`

## Troubleshooting

### Lỗi: "No such table"
- Chạy lại: `py init_new_data.py` hoặc `py run.py`

### Lỗi: "Database is locked"
- Đóng tất cả kết nối đến database
- Xóa file `instance/app.db` và tạo lại

### Lỗi: "Module not found"
- Cài đặt lại: `py -m pip install -r requirements.txt`





