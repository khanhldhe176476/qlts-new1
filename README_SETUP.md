# 🚀 Hướng Dẫn Setup Nhanh

## Sau khi clone code từ GitHub

### Windows

1. **Cài đặt thư viện:**
```bash
py -m pip install -r requirements.txt
```

2. **Khởi tạo database và dữ liệu:**
```bash
py init_new_data.py
```

Hoặc chạy script tự động:
```bash
setup.bat
```

3. **Chạy ứng dụng:**
```bash
py run.py
```

4. **Truy cập:**
- Web: http://localhost:5000/
- API Docs: http://localhost:5000/api/v1/docs/

5. **Đăng nhập:**
- Username: `admin`
- Password: `admin123`

---

## ⚠️ Tại sao không có dữ liệu?

1. **Database file không được commit lên GitHub**
   - File `instance/app.db` được thêm vào `.gitignore`
   - Mỗi developer cần tạo database riêng

2. **Cần chạy script khởi tạo**
   - `init_new_data.py` - Tạo database và dữ liệu mẫu
   - `run.py` - Tự động tạo database và admin user khi chạy lần đầu

---

## 📋 Checklist Setup

- [ ] Cài đặt Python 3.8+
- [ ] Cài đặt thư viện: `py -m pip install -r requirements.txt`
- [ ] Khởi tạo database: `py init_new_data.py`
- [ ] Chạy ứng dụng: `py run.py`
- [ ] Kiểm tra: http://localhost:5000/

---

## 🔧 Troubleshooting

**Lỗi: "No such table"**
→ Chạy: `py init_new_data.py`

**Lỗi: "Module not found"**
→ Chạy: `py -m pip install -r requirements.txt`

**Lỗi: "Database is locked"**
→ Xóa `instance/app.db` và chạy lại `py init_new_data.py`

---

## 📚 Tài liệu

- `SETUP.md` - Hướng dẫn chi tiết
- `API_DOCS.md` - Tài liệu API
- `DATA_INTEGRITY.md` - Đảm bảo tính toàn vẹn dữ liệu





