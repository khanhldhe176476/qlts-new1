# Hướng Dẫn Test Tính Năng Bàn Giao Tài Sản

## 🎯 Mục Đích Test

Kiểm tra toàn bộ quy trình bàn giao tài sản từ tạo yêu cầu → gửi email → xác nhận → cập nhật tự động.

## 📋 Chuẩn Bị

### 1. Cài đặt Dependencies

```bash
cd QLTaiSan
pip install -r requirements.txt
```

### 2. Tạo Dữ Liệu Test

Chạy script để tạo dữ liệu test:

```bash
python test_transfer.py
```

Hoặc chạy script init data:

```bash
python init_new_data.py
```

### 3. Cấu Hình Email (Tùy chọn)

Nếu muốn test gửi email thật, thêm vào file `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
APP_URL=http://localhost:5000
```

**Lưu ý:** Nếu không cấu hình email, bạn vẫn có thể test bằng cách lấy link từ danh sách bàn giao.

## 🧪 Các Bước Test

### Test Case 1: Tạo Bàn Giao Thành Công

**Mục tiêu:** Kiểm tra tạo yêu cầu bàn giao và gửi email

**Các bước:**
1. Đăng nhập với tài khoản `admin` / `mh123#@!`
2. Vào menu **"Bàn giao tài sản"** → **"Tạo bàn giao mới"**
3. Điền form:
   - Chọn tài sản: "Laptop Test" (hoặc tài sản khác)
   - Chọn người nhận: "user1" hoặc "user2"
   - Số lượng: 2
   - Ghi chú: "Test bàn giao"
4. Click **"Gửi yêu cầu bàn giao"**

**Kết quả mong đợi:**
- ✅ Hiển thị thông báo thành công
- ✅ Nếu có email: Email được gửi đến người nhận
- ✅ Nếu không có email: Hiển thị mã bàn giao và link xác nhận
- ✅ Bàn giao xuất hiện trong danh sách với trạng thái "Chờ xác nhận"

---

### Test Case 2: Xác Nhận Bàn Giao Qua Email Link

**Mục tiêu:** Kiểm tra xác nhận bàn giao qua link trong email

**Các bước:**
1. **Lấy link xác nhận:**
   - Cách 1: Kiểm tra email của người nhận
   - Cách 2: Vào danh sách bàn giao → Click icon link ở cột "Thao tác"
   
2. **Mở link trong trình duyệt** (có thể dùng trình duyệt ẩn danh để test như người nhận)

3. **Kiểm tra trang xác nhận:**
   - Hiển thị đầy đủ thông tin bàn giao
   - Mã bàn giao
   - Tên tài sản
   - Số lượng dự kiến
   - Form nhập số lượng

4. **Xác nhận:**
   - Nhập số lượng: 2 (đầy đủ)
   - Click **"Xác nhận bàn giao"**

**Kết quả mong đợi:**
- ✅ Hiển thị trang "Xác nhận thành công"
- ✅ Thông báo tài sản đã được cập nhật
- ✅ Trạng thái bàn giao chuyển thành "Đã xác nhận"

---

### Test Case 3: Xác Nhận Từng Phần

**Mục tiêu:** Kiểm tra xác nhận từng phần (không đầy đủ)

**Các bước:**
1. Tạo bàn giao mới với số lượng: 5
2. Mở link xác nhận
3. Nhập số lượng: 3 (chưa đầy đủ)
4. Click xác nhận

**Kết quả mong đợi:**
- ✅ Hiển thị cảnh báo: "Đã xác nhận 3/5 thiết bị"
- ✅ Trạng thái vẫn là "Chờ xác nhận"
- ✅ Tài sản CHƯA được cập nhật
- ✅ Có thể xác nhận lại với số lượng cao hơn

5. Xác nhận lại với số lượng: 5 (đầy đủ)

**Kết quả mong đợi:**
- ✅ Trạng thái chuyển thành "Đã xác nhận"
- ✅ Tài sản được cập nhật tự động

---

### Test Case 4: Kiểm Tra Cập Nhật Tài Sản

**Mục tiêu:** Kiểm tra tài sản được cập nhật đúng sau khi xác nhận

**Các bước:**
1. Ghi nhận số lượng tài sản ban đầu của người gửi
2. Tạo và xác nhận bàn giao đầy đủ
3. Kiểm tra:
   - Số lượng tài sản của người gửi đã giảm
   - Số lượng tài sản của người nhận đã tăng (hoặc tài sản mới được tạo)

**Kết quả mong đợi:**
- ✅ Số lượng người gửi giảm đúng
- ✅ Số lượng người nhận tăng đúng
- ✅ Nếu người nhận đã có tài sản tương tự → merge số lượng
- ✅ Nếu chưa có → tạo tài sản mới

---

### Test Case 5: Test Link Hết Hạn

**Mục tiêu:** Kiểm tra xử lý khi link hết hạn

**Các bước:**
1. Tạo bàn giao
2. Manually set `token_expires_at` trong database về quá khứ
3. Mở link xác nhận

**Kết quả mong đợi:**
- ✅ Hiển thị trang "Link đã hết hạn"
- ✅ Không cho phép xác nhận

---

### Test Case 6: Test Validation

**Mục tiêu:** Kiểm tra các validation

**Test các trường hợp:**
1. **Số lượng = 0:**
   - Tạo bàn giao với số lượng 0 → ❌ Báo lỗi
   
2. **Số lượng > số lượng hiện có:**
   - Tài sản có 5, bàn giao 10 → ❌ Báo lỗi
   
3. **Xác nhận số lượng < 0:**
   - Nhập -1 → ❌ Báo lỗi
   
4. **Xác nhận số lượng > số lượng dự kiến:**
   - Dự kiến 5, nhập 10 → ❌ Báo lỗi

---

### Test Case 7: Test Phân Quyền

**Mục tiêu:** Kiểm tra user chỉ thấy bàn giao của mình

**Các bước:**
1. Đăng nhập với `user1`
2. Vào danh sách bàn giao
3. Kiểm tra chỉ thấy:
   - Bàn giao user1 gửi
   - Bàn giao user1 nhận
4. Đăng nhập với `admin`
5. Kiểm tra thấy TẤT CẢ bàn giao

---

## 🔍 Kiểm Tra Database

### Xem bàn giao trong database:

```python
from app import app, db
from models import AssetTransfer

with app.app_context():
    transfers = AssetTransfer.query.all()
    for t in transfers:
        print(f"{t.transfer_code}: {t.asset.name} - {t.status}")
        print(f"  Token: {t.confirmation_token}")
        print(f"  Link: http://localhost:5000/transfer/confirm/{t.confirmation_token}")
```

### Xem tài sản đã cập nhật:

```python
from app import app, db
from models import Asset, User

with app.app_context():
    user = User.query.filter_by(username='user1').first()
    assets = Asset.query.filter_by(user_id=user.id).all()
    for a in assets:
        print(f"{a.name}: {a.quantity}")
```

---

## 📝 Checklist Test

- [ ] Tạo bàn giao thành công
- [ ] Email được gửi (nếu có cấu hình)
- [ ] Link xác nhận hoạt động
- [ ] Xác nhận đầy đủ → tài sản cập nhật
- [ ] Xác nhận từng phần → chưa cập nhật
- [ ] Xác nhận lại đầy đủ → tài sản cập nhật
- [ ] Link hết hạn → hiển thị thông báo
- [ ] Validation số lượng hoạt động
- [ ] Phân quyền hoạt động đúng
- [ ] Audit log được ghi

---

## 🐛 Troubleshooting

### Email không gửi được:
```bash
# Test kết nối email
python -c "from app import app, mail; app.app_context().push(); mail.connect()"
```

### Link không hoạt động:
- Kiểm tra token trong database
- Kiểm tra URL đúng format
- Kiểm tra token chưa hết hạn

### Tài sản không cập nhật:
- Kiểm tra đã xác nhận đầy đủ chưa
- Kiểm tra số lượng tài sản gốc còn đủ
- Xem log trong console

---

## 🎬 Test Nhanh (Quick Test)

1. **Tạo bàn giao:**
   ```
   Đăng nhập → Bàn giao tài sản → Tạo mới
   Chọn: Laptop Test → user1 → Số lượng: 2
   ```

2. **Lấy link:**
   ```
   Danh sách bàn giao → Click icon link
   Copy URL
   ```

3. **Xác nhận:**
   ```
   Mở URL trong trình duyệt
   Nhập số lượng: 2
   Click xác nhận
   ```

4. **Kiểm tra:**
   ```
   Vào Tài sản → Tìm tài sản của user1
   Kiểm tra số lượng đã tăng
   ```

---

## ✅ Kết Quả Mong Đợi

Sau khi test xong, bạn sẽ thấy:
- ✅ Bàn giao được tạo và lưu trong database
- ✅ Email được gửi (nếu có cấu hình)
- ✅ Link xác nhận hoạt động
- ✅ Tài sản tự động cập nhật khi xác nhận đầy đủ
- ✅ Audit log ghi nhận mọi thao tác

