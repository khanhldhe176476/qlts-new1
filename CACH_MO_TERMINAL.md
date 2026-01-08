# Cách mở Terminal trên Windows

## 🚀 Các cách mở Terminal

### Cách 1: Mở PowerShell (Khuyến nghị)

**Phương pháp nhanh nhất:**
1. Nhấn phím **Windows** trên bàn phím
2. Gõ: `powershell`
3. Nhấn **Enter**

**Hoặc:**
1. Nhấn tổ hợp phím: **Windows + X**
2. Chọn **Windows PowerShell** hoặc **Terminal**

**Hoặc:**
1. Nhấn tổ hợp phím: **Windows + R**
2. Gõ: `powershell`
3. Nhấn **Enter**

### Cách 2: Mở Command Prompt (CMD)

**Phương pháp nhanh:**
1. Nhấn phím **Windows**
2. Gõ: `cmd`
3. Nhấn **Enter**

**Hoặc:**
1. Nhấn tổ hợp phím: **Windows + R**
2. Gõ: `cmd`
3. Nhấn **Enter**

### Cách 3: Mở Terminal trong Docker Desktop

1. Mở **Docker Desktop**
2. Click vào biểu tượng **Settings** (bánh răng) ở góc trên bên phải
3. Vào **General** → Tìm **Use integrated terminal**
4. Hoặc click vào biểu tượng **Terminal** trong Docker Desktop (nếu có)

**Lưu ý:** Cách này không phải lúc nào cũng có, nên dùng Cách 1 hoặc 2.

### Cách 4: Mở Terminal từ File Explorer

1. Mở **File Explorer** (Windows + E)
2. Điều hướng đến thư mục: `D:\QLTS\QLTSC\qlts-new8`
3. Click vào thanh địa chỉ (address bar)
4. Gõ: `powershell` hoặc `cmd`
5. Nhấn **Enter**

**Hoặc:**
1. Mở **File Explorer**
2. Điều hướng đến: `D:\QLTS\QLTSC\qlts-new8`
3. Click chuột phải vào thư mục `qlts-new8`
4. Chọn **Open in Terminal** (nếu có) hoặc **Open PowerShell window here**

## ✅ Kiểm tra Terminal đã mở đúng chưa

Sau khi mở Terminal, bạn sẽ thấy một cửa sổ đen (CMD) hoặc cửa sổ xanh (PowerShell) với dòng lệnh như:

```
PS C:\Users\YourName>
```
hoặc
```
C:\Users\YourName>
```

## 📝 Các lệnh cơ bản

### Di chuyển đến thư mục dự án:
```bash
cd D:\QLTS\QLTSC\qlts-new8
```

### Kiểm tra đã ở đúng thư mục chưa:
```bash
dir
```
hoặc (trong PowerShell):
```bash
ls
```

Bạn sẽ thấy các file như: `docker-compose.yml`, `Dockerfile`, `app.py`, v.v.

### Chạy Docker Compose:
```bash
docker compose up --build
```

## 🎯 Hướng dẫn từng bước chi tiết

### Bước 1: Mở Terminal
- Nhấn **Windows** → Gõ `powershell` → Nhấn **Enter**

### Bước 2: Di chuyển đến thư mục
- Gõ: `cd D:\QLTS\QLTSC\qlts-new8`
- Nhấn **Enter**

### Bước 3: Kiểm tra
- Gõ: `dir` (hoặc `ls` trong PowerShell)
- Nhấn **Enter**
- Bạn sẽ thấy danh sách file trong thư mục

### Bước 4: Chạy Docker
- Gõ: `docker compose up --build`
- Nhấn **Enter**

## ⚠️ Lưu ý

1. **PowerShell vs CMD**: Cả hai đều dùng được, nhưng PowerShell mạnh hơn
2. **Quyền Administrator**: Thường không cần, nhưng nếu gặp lỗi permission, có thể cần chạy với quyền Admin:
   - Click chuột phải vào PowerShell/CMD
   - Chọn **Run as administrator**

## 🖼️ Mô tả giao diện

**PowerShell:**
- Cửa sổ màu xanh dương
- Dòng lệnh bắt đầu bằng `PS C:\...>`

**Command Prompt (CMD):**
- Cửa sổ màu đen
- Dòng lệnh bắt đầu bằng `C:\...>`

Cả hai đều dùng được cho Docker!



