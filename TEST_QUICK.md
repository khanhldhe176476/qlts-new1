# 🚀 Hướng Dẫn Test Nhanh Bàn Giao Tài Sản

## ⚡ Test Nhanh (5 phút)

### Bước 1: Chuẩn bị dữ liệu

```bash
cd QLTaiSan
python init_new_data.py
```

Hoặc đảm bảo đã có:
- Tài khoản admin: `admin` / `mh123#@!`
- Tài khoản user: `user1` / `mh123#@!`
- Ít nhất 1 tài sản với số lượng > 0

### Bước 2: Tạo bàn giao

1. **Đăng nhập:** `http://localhost:5000/login`
   - Username: `admin`
   - Password: `mh123#@!`

2. **Vào menu:** "Bàn giao tài sản" → "Tạo bàn giao mới"

3. **Điền form:**
   - Tài sản: Chọn bất kỳ tài sản nào
   - Người nhận: Chọn `user1` hoặc `user2`
   - Số lượng: 2
   - Ghi chú: "Test bàn giao"

4. **Click:** "Gửi yêu cầu bàn giao"

### Bước 3: Lấy link xác nhận

**Cách 1: Từ danh sách bàn giao**
1. Vào "Bàn giao tài sản" → Xem danh sách
2. Tìm bàn giao vừa tạo
3. Click icon **🔗** ở cột "Thao tác"
4. Copy URL

**Cách 2: Từ database (nếu biết SQL)**
```sql
SELECT confirmation_token FROM asset_transfer ORDER BY id DESC LIMIT 1;
```
URL: `http://localhost:5000/transfer/confirm/{token}`

### Bước 4: Xác nhận bàn giao

1. **Mở link** trong trình duyệt (có thể dùng trình duyệt ẩn danh)

2. **Kiểm tra thông tin:**
   - Mã bàn giao
   - Tên tài sản
   - Số lượng dự kiến

3. **Nhập số lượng:** 2 (hoặc số lượng bạn muốn test)

4. **Click:** "Xác nhận bàn giao"

### Bước 5: Kiểm tra kết quả

1. **Kiểm tra thông báo:**
   - Nếu xác nhận đầy đủ → "Đã xác nhận bàn giao thành công!"
   - Nếu chưa đầy đủ → "Đã xác nhận X/Y thiết bị..."

2. **Kiểm tra tài sản:**
   - Vào "Tài sản"
   - Tìm tài sản của người nhận
   - Kiểm tra số lượng đã tăng

3. **Kiểm tra danh sách bàn giao:**
   - Trạng thái đã chuyển thành "Đã xác nhận" (nếu đầy đủ)

---

## 🧪 Test Các Trường Hợp

### Test 1: Xác nhận đầy đủ ✅

- Tạo bàn giao: Số lượng 3
- Xác nhận: 3
- **Kết quả:** Tài sản được cập nhật ngay

### Test 2: Xác nhận từng phần ⚠️

- Tạo bàn giao: Số lượng 5
- Xác nhận lần 1: 3
- **Kết quả:** Chưa cập nhật, trạng thái "Chờ xác nhận"
- Xác nhận lần 2: 5
- **Kết quả:** Tài sản được cập nhật

### Test 3: Validation ❌

- Tạo bàn giao với số lượng 0 → ❌ Lỗi
- Tạo bàn giao với số lượng > số lượng hiện có → ❌ Lỗi
- Xác nhận với số lượng < 0 → ❌ Lỗi

### Test 4: Link hết hạn ⏰

- Tạo bàn giao
- Sửa `token_expires_at` trong database về quá khứ
- Mở link → Hiển thị "Link đã hết hạn"

---

## 📧 Test Email (Nếu có cấu hình)

### Cấu hình Gmail:

1. Vào Google Account → Security
2. Bật 2-Step Verification
3. Tạo App Password
4. Thêm vào `.env`:
   ```env
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-char-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   APP_URL=http://localhost:5000
   ```

5. Restart server
6. Tạo bàn giao → Kiểm tra email

---

## 🔍 Debug

### Xem tất cả bàn giao:

```python
from app import app, db
from models import AssetTransfer

with app.app_context():
    for t in AssetTransfer.query.all():
        print(f"{t.transfer_code}: {t.asset.name}")
        print(f"  Status: {t.status}")
        print(f"  Confirmed: {t.confirmed_quantity}/{t.expected_quantity}")
        print(f"  Link: http://localhost:5000/transfer/confirm/{t.confirmation_token}")
        print()
```

### Xem tài sản đã cập nhật:

```python
from app import app, db
from models import Asset, User

with app.app_context():
    user = User.query.filter_by(username='user1').first()
    if user:
        assets = Asset.query.filter_by(user_id=user.id).all()
        for a in assets:
            print(f"{a.name}: {a.quantity} - {a.notes}")
```

---

## ✅ Checklist

- [ ] Tạo bàn giao thành công
- [ ] Link xác nhận hoạt động
- [ ] Xác nhận đầy đủ → tài sản cập nhật
- [ ] Xác nhận từng phần → chưa cập nhật
- [ ] Validation hoạt động
- [ ] Phân quyền đúng (user chỉ thấy của mình)

---

## 🎯 Test Nhanh Nhất

**3 bước:**

1. **Tạo:** Admin → Bàn giao → Tạo mới → Chọn tài sản + user1 → Số lượng 2
2. **Lấy link:** Danh sách bàn giao → Click icon link
3. **Xác nhận:** Mở link → Nhập 2 → Xác nhận

**Kiểm tra:** Vào Tài sản → Tìm của user1 → Số lượng đã tăng!

