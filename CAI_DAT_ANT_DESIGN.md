# Hướng dẫn cài đặt và chạy hệ thống với Ant Design

## Bước 1: Cài đặt Python dependencies

```bash
cd qlts-new8
pip install -r requirements.txt
```

## Bước 2: Cài đặt Node.js dependencies

```bash
cd frontend
npm install
```

## Bước 3: Chạy Development

### Terminal 1: Flask Backend
```bash
cd qlts-new8
py run.py
```
Backend sẽ chạy tại: http://127.0.0.1:5000

### Terminal 2: React Frontend
```bash
cd frontend
npm run dev
```
Frontend sẽ chạy tại: http://localhost:3000

## Bước 4: Build cho Production

```bash
cd frontend
npm run build
```

Sau khi build, files sẽ được tạo trong `static/frontend/`

## Cấu trúc API

Tất cả API endpoints đều có prefix `/api/v1/`:

- `/api/v1/auth/login` - Đăng nhập
- `/api/v1/auth/me` - Lấy thông tin user hiện tại
- `/api/v1/assets` - Quản lý tài sản
- `/api/v1/asset-types` - Quản lý loại tài sản
- `/api/v1/users` - Quản lý người dùng
- `/api/v1/maintenance` - Quản lý bảo trì
- `/api/v1/transfers` - Quản lý bàn giao

## Tính năng đã hoàn thiện

✅ Layout với Ant Design
✅ Đăng nhập/Đăng xuất
✅ Dashboard với thống kê
✅ Quản lý tài sản (CRUD đầy đủ)
✅ Quản lý loại tài sản (CRUD đầy đủ)
✅ Quản lý người dùng (CRUD đầy đủ)
✅ Quản lý bảo trì (CRUD đầy đủ)
✅ Quản lý bàn giao
✅ Thùng rác (khôi phục, xóa vĩnh viễn)
✅ Import/Export Excel
✅ Tìm kiếm và lọc
✅ Responsive design

## Lưu ý

1. Đảm bảo Flask API đang chạy trước khi chạy frontend
2. CORS đã được cấu hình để cho phép frontend kết nối
3. Authentication sử dụng JWT token
4. Tất cả API calls đều qua axios với error handling

## Troubleshooting

### Lỗi: Cannot find module
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Lỗi: Port already in use
Thay đổi port trong `vite.config.js` hoặc `run.py`

### Lỗi: API không kết nối được
- Kiểm tra Flask đang chạy tại port 5000
- Kiểm tra CORS settings trong `app.py`
- Kiểm tra proxy config trong `vite.config.js`




















