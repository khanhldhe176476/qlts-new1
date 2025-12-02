# 📖 HƯỚNG DẪN SỬ DỤNG TÍNH NĂNG BÀN GIAO TÀI SẢN

## 🎯 TỔNG QUAN

Tính năng bàn giao tài sản cho phép:
- ✅ **Gửi email tự động** đến nhân viên khi tạo bàn giao
- ✅ **Xác nhận qua email** - Nhân viên click link trong email để xác nhận
- ✅ **Tự động cập nhật** - Hệ thống tự động cập nhật tài sản sau khi xác nhận

---

## 📋 QUY TRÌNH SỬ DỤNG

### BƯỚC 1: Tạo Bàn Giao Tài Sản

1. Đăng nhập vào hệ thống
2. Vào menu **"Bàn giao tài sản"** → **"Tạo bàn giao mới"**
3. Điền thông tin:
   - **Tài sản bàn giao**: Chọn tài sản cần bàn giao
   - **Người nhận**: Chọn nhân viên (phải có email)
   - **Số lượng**: Nhập số lượng thiết bị
   - **Ghi chú**: (Tùy chọn)
4. Click **"Gửi yêu cầu bàn giao và Email xác nhận"**

**✅ Hệ thống sẽ tự động:**
- Tạo bàn giao trong hệ thống
- **Gửi email ngay lập tức** đến nhân viên được chọn
- Hiển thị thông báo thành công

---

### BƯỚC 2: Nhân Viên Nhận Email

Nhân viên sẽ nhận email với:
- **Tiêu đề**: "Xác nhận bàn giao tài sản - [Mã bàn giao]"
- **Nội dung**: 
  - Thông tin bàn giao
  - Số lượng dự kiến
  - **Link xác nhận** (có hiệu lực 7 ngày)

**⚠️ Lưu ý**: 
- Kiểm tra thư mục **SPAM** nếu không thấy email
- Link có hiệu lực 7 ngày

---

### BƯỚC 3: Nhân Viên Xác Nhận

1. Nhân viên click **link xác nhận** trong email
2. Trang xác nhận hiển thị:
   - Thông tin bàn giao
   - Số lượng dự kiến
3. Nhân viên nhập **số lượng thiết bị thực tế nhận được**
4. Click **"Xác nhận bàn giao"**

**✅ Hệ thống sẽ tự động:**
- Cập nhật số lượng xác nhận
- Nếu xác nhận đầy đủ:
  - ✅ **Giảm** số lượng tài sản của người gửi
  - ✅ **Tăng** số lượng tài sản của người nhận (hoặc tạo mới nếu chưa có)
  - ✅ Đánh dấu bàn giao là "Đã xác nhận"
  - ✅ Ghi nhận trong audit log

---

### BƯỚC 4: Kiểm Tra Kết Quả

**Người gửi:**
- Vào **"Bàn giao tài sản"** → Xem danh sách
- Bàn giao sẽ hiển thị trạng thái "Đã xác nhận"
- Số lượng tài sản đã được giảm

**Người nhận:**
- Đăng nhập vào hệ thống
- Vào **"Tài sản"** → Xem danh sách
- Tài sản đã được thêm vào (hoặc số lượng đã tăng)

---

## 🔄 CÁC TÍNH NĂNG KHÁC

### Gửi Lại Email

Nếu nhân viên chưa nhận được email:

1. Vào **"Bàn giao tài sản"** → Xem danh sách
2. Tìm bàn giao cần gửi lại email
3. Click nút **icon envelope** (màu vàng)
4. Email sẽ được gửi lại ngay lập tức

### Gửi Email Test

Để test gửi email:

1. Vào **"Bàn giao tài sản"** → Click **"Gửi Email"**
2. Chọn nhân viên từ danh sách
3. Click **"Gửi Email"**
4. Kiểm tra email của nhân viên

---

## ⚠️ LƯU Ý QUAN TRỌNG

1. **Email phải được cấu hình** trong file `.env` để gửi email tự động
2. **Nhân viên phải có email** trong hệ thống
3. **Link xác nhận có hiệu lực 7 ngày** - Sau đó sẽ hết hạn
4. **Chỉ xác nhận đầy đủ mới cập nhật tài sản** - Xác nhận từng phần chỉ lưu tiến độ
5. **Kiểm tra SPAM folder** nếu không thấy email

---

## ❓ XỬ LÝ SỰ CỐ

### Email không được gửi?

1. Kiểm tra cấu hình email trong file `.env`
2. Xem file `HUONG_DAN_GMAIL.md` để cấu hình Gmail
3. Kiểm tra log trong console để xem lỗi

### Nhân viên không nhận được email?

1. Kiểm tra thư mục **SPAM**
2. Kiểm tra email nhân viên có đúng không
3. Gửi lại email từ danh sách bàn giao

### Tài sản không được cập nhật?

1. Đảm bảo nhân viên đã xác nhận **đầy đủ** số lượng
2. Kiểm tra log trong console
3. Kiểm tra audit log để xem lịch sử

---

## 📚 TÀI LIỆU LIÊN QUAN

- `HUONG_DAN_GMAIL.md` - Hướng dẫn cấu hình Gmail
- `QUICK_START_GMAIL.md` - Quick start cho Gmail
- `KHAC_PHUC_EMAIL.md` - Khắc phục sự cố email
- `EMAIL_GUIDE.md` - Hướng dẫn sử dụng tính năng email

---

**Chúc bạn sử dụng thành công! 🎉**

