# Hướng dẫn Build và Chạy Project với Docker Desktop

## Công nghệ sử dụng

Dự án này sử dụng:
- **Backend**: Flask (Python 3.11) với SQLAlchemy
- **Frontend**: React 18 + Vite + Ant Design
- **Database**: PostgreSQL 15 (trong Docker) hoặc SQLite
- **Web Server**: Nginx (reverse proxy)

## Yêu cầu

1. **Docker Desktop** đã được cài đặt và đang chạy
2. Đảm bảo Docker Desktop đã khởi động (icon Docker ở system tray)
3. **Windows**: Docker Desktop for Windows
4. **RAM**: Tối thiểu 4GB (khuyến nghị 8GB)
5. **Disk**: Ít nhất 10GB trống

## Quick Start (Bắt đầu nhanh)

### Bước 1: Kiểm tra Docker Desktop
- Mở Docker Desktop
- Đợi đến khi icon Docker ở system tray không còn loading
- Kiểm tra status: "Docker Desktop is running"

### Bước 2: Mở Terminal
- Mở **PowerShell** hoặc **Command Prompt**
- Hoặc click **Terminal** trong Docker Desktop

### Bước 3: Chạy lệnh
```bash
cd D:\QLTS\QLTSC\qlts-new8
docker-compose up --build
```

### Bước 4: Đợi build xong
- Lần đầu sẽ mất 5-10 phút (download images, build frontend, install dependencies)
- Bạn sẽ thấy logs trong terminal
- Khi thấy "Running on http://0.0.0.0:5000" = thành công!

### Bước 5: Mở trình duyệt
- Truy cập: **http://localhost**
- Hoặc: **http://localhost:5000**
- Đăng nhập: `admin` / `admin123`

## Cách Build và Chạy

### Phương pháp 1: Sử dụng Docker Desktop GUI (Giao diện đồ họa)

#### Bước 1: Mở Docker Desktop
1. Khởi động **Docker Desktop** từ Start Menu
2. Đợi Docker Desktop khởi động hoàn toàn (icon Docker ở system tray không còn loading)
3. Mở Docker Desktop window

#### Bước 2: Mở Terminal trong Docker Desktop
1. Trong Docker Desktop, click vào biểu tượng **Terminal** (hoặc Settings → General → Enable integrated terminal)
2. Hoặc mở **PowerShell** hoặc **Command Prompt** riêng

#### Bước 3: Di chuyển đến thư mục dự án
Trong terminal, gõ lệnh:
```bash
cd D:\QLTS\QLTSC\qlts-new8
```

#### Bước 4: Build và chạy containers
Gõ lệnh sau để build và chạy:
```bash
docker-compose up --build
```

**Hoặc** chạy ở background (detached mode - không hiển thị logs):
```bash
docker-compose up -d --build
```

#### Bước 5: Kiểm tra containers trong Docker Desktop
1. Mở Docker Desktop
2. Vào tab **Containers** (bên trái)
3. Bạn sẽ thấy 3 containers:
   - `qlts-nginx` (Nginx)
   - `qlts-web` (Flask app)
   - `qlts-db` (PostgreSQL)
4. Tất cả containers phải có status **Running** (màu xanh)

#### Quản lý containers qua Docker Desktop GUI:

**Xem logs:**
- Click vào container name (ví dụ: `qlts-web`)
- Tab **Logs** sẽ hiển thị logs của container đó

**Dừng containers:**
- Click vào nút **Stop** (biểu tượng vuông) ở mỗi container
- Hoặc chọn nhiều containers và click **Stop** ở trên

**Xóa containers:**
- Click vào nút **Delete** (thùng rác) ở mỗi container
- Hoặc chọn nhiều containers và click **Delete** ở trên

**Restart containers:**
- Click vào nút **Restart** (mũi tên tròn) ở mỗi container

**Xem resource usage:**
- Click vào container để xem CPU, Memory usage trong tab **Stats**

### Phương pháp 2: Sử dụng Docker Desktop Compose (Từ Docker Desktop 4.0+)

Nếu Docker Desktop của bạn hỗ trợ Compose (phiên bản mới):

1. Mở **Docker Desktop**
2. Vào tab **Compose** (hoặc **Containers** → **Compose**)
3. Click **Open** hoặc **Import Compose File**
4. Chọn file `docker-compose.yml` trong thư mục `D:\QLTS\QLTSC\qlts-new8`
5. Docker Desktop sẽ tự động build và chạy các services

### Phương pháp 3: Sử dụng Command Line (Terminal)

#### Bước 1: Mở Terminal
- Mở **PowerShell** hoặc **Command Prompt**
- Hoặc mở terminal trong Docker Desktop

#### Bước 2: Di chuyển đến thư mục dự án
```bash
cd D:\QLTS\QLTSC\qlts-new8
```

#### Bước 3: Build Docker image
```bash
docker-compose build
```

#### Bước 4: Chạy containers
```bash
docker-compose up -d
```

#### Bước 5: Xem logs (nếu cần)
```bash
docker-compose logs -f
```

## Truy cập ứng dụng

Sau khi build và chạy thành công, truy cập:

- **URL chính**: http://localhost (port 80)
- **URL trực tiếp Flask**: http://localhost:5000
- **Tài khoản mặc định**:
  - Username: `admin`
  - Password: `admin123` (hoặc theo cấu hình trong docker-compose.yml)

## Quản lý Containers

### Xem trạng thái containers
```bash
docker-compose ps
```

### Dừng containers
```bash
docker-compose stop
```

### Dừng và xóa containers
```bash
docker-compose down
```

### Dừng và xóa tất cả (bao gồm volumes - xóa database)
```bash
docker-compose down -v
```

### Xem logs của từng service
```bash
# Tất cả services
docker-compose logs -f

# Chỉ Nginx
docker-compose logs -f nginx

# Chỉ Flask app
docker-compose logs -f web

# Chỉ database
docker-compose logs -f db
```

### Rebuild lại từ đầu
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Cấu hình

### Thay đổi biến môi trường

Sửa file `docker-compose.yml` trong phần `environment` của service `web`:

```yaml
environment:
  - DATABASE_URL=postgresql://qlts_user:qlts_password@db:5432/qlts_db
  - SECRET_KEY=your-secret-key-change-in-production
  - ADMIN_USERNAME=admin
  - ADMIN_PASSWORD=your-password
  - ADMIN_EMAIL=admin@example.com
```

### Thay đổi port

Sửa trong `docker-compose.yml`:

```yaml
nginx:
  ports:
    - "8080:80"  # Thay đổi 8080 thành port bạn muốn
```

## Kiểm tra Health

```bash
# Kiểm tra health endpoint
curl http://localhost/healthz

# Hoặc mở trình duyệt
# http://localhost/healthz
```

## Troubleshooting

### Lỗi: Port đã được sử dụng

Nếu port 80 hoặc 5000 đã được sử dụng:
1. Thay đổi port trong `docker-compose.yml`
2. Hoặc dừng service đang sử dụng port đó

### Lỗi: Cannot connect to database

Đảm bảo service `db` đã start xong:
```bash
docker-compose up db
# Đợi vài giây
docker-compose up web nginx
```

### Lỗi: Frontend không hiển thị

1. Kiểm tra xem frontend đã được build chưa:
   ```bash
   docker-compose exec web ls -la static/frontend
   ```
2. Nếu không có, rebuild lại:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Lỗi: Permission denied

Trên Linux/Mac:
```bash
sudo chown -R $USER:$USER instance/
```

### Xóa tất cả và bắt đầu lại

```bash
# Dừng và xóa containers, networks, volumes
docker-compose down -v

# Xóa images
docker rmi qlts-new8-web

# Build lại từ đầu
docker-compose build --no-cache
docker-compose up -d
```

## Cấu trúc Docker

- **nginx**: Reverse proxy, serve trên port 80
- **web**: Flask application, chạy trên port 5000 (internal)
- **db**: PostgreSQL database, port 5432 (internal), expose 5433 (localhost)

## Lưu ý

1. **Database**: Dữ liệu được lưu trong Docker volume `postgres_data`. Nếu xóa volume, dữ liệu sẽ mất.
2. **Instance folder**: Thư mục `instance/` được mount vào container để persist SQLite (nếu dùng) và exports.
3. **Frontend**: Frontend được build trong Docker image, không cần build riêng.
4. **Environment variables**: Có thể tạo file `.env` và sử dụng trong `docker-compose.yml`.

## Build chỉ một service

```bash
# Build chỉ web service
docker-compose build web

# Build chỉ nginx (thường không cần vì dùng image có sẵn)
docker-compose build nginx
```

## Xem resource usage trong Docker Desktop

1. Mở **Docker Desktop**
2. Vào tab **Containers**
3. Click vào một container để xem:
   - **Stats**: CPU, Memory, Network, Disk I/O usage
   - **Logs**: Real-time logs
   - **Inspect**: Chi tiết cấu hình container
   - **Files**: Xem files trong container (nếu có quyền)

4. Vào tab **Images** để xem:
   - Danh sách images
   - Size của mỗi image
   - Có thể xóa images không dùng

5. Vào tab **Volumes** để xem:
   - Danh sách volumes (bao gồm `postgres_data`)
   - Size của volumes
   - Có thể xóa volumes (⚠️ sẽ mất dữ liệu)

## Hướng dẫn chi tiết Docker Desktop GUI

### Kiểm tra Docker Desktop đã chạy chưa

1. Nhìn vào **system tray** (góc dưới bên phải màn hình Windows)
2. Tìm icon **Docker** (con cá voi)
3. Nếu icon đang quay = Docker đang khởi động
4. Nếu icon tĩnh = Docker đã sẵn sàng
5. Nếu không thấy icon = Docker chưa chạy → Mở Docker Desktop từ Start Menu

### Xem trạng thái containers

1. Mở **Docker Desktop**
2. Click **Containers** ở sidebar bên trái
3. Bạn sẽ thấy danh sách containers:
   - ✅ **Running** (màu xanh) = Đang chạy
   - ⏸️ **Exited** (màu xám) = Đã dừng
   - 🔄 **Restarting** = Đang khởi động lại
   - ⚠️ **Error** (màu đỏ) = Có lỗi

### Xem logs trong Docker Desktop

1. Click vào tên container (ví dụ: `qlts-web`)
2. Tab **Logs** sẽ hiển thị
3. Logs tự động refresh
4. Có thể copy logs bằng cách chọn text và Ctrl+C

### Dừng/Tạm dừng containers

**Cách 1: Dừng một container**
1. Tìm container trong danh sách
2. Click nút **Stop** (biểu tượng vuông) ở bên phải

**Cách 2: Dừng tất cả containers của project**
1. Chọn tất cả containers (qlts-nginx, qlts-web, qlts-db)
2. Click **Stop** ở thanh công cụ phía trên

### Xóa containers

⚠️ **Cảnh báo**: Xóa container sẽ xóa container nhưng không xóa volumes (dữ liệu database vẫn còn)

1. Dừng container trước (nếu đang chạy)
2. Click nút **Delete** (thùng rác) ở bên phải container
3. Xác nhận xóa

### Xóa volumes (Xóa dữ liệu database)

⚠️ **Cảnh báo**: Xóa volume sẽ xóa toàn bộ dữ liệu database!

1. Vào tab **Volumes** trong Docker Desktop
2. Tìm volume `qlts-new8_postgres_data` hoặc `postgres_data`
3. Click nút **Delete** (thùng rác)
4. Xác nhận xóa

### Rebuild images trong Docker Desktop

**Cách 1: Qua Terminal trong Docker Desktop**
1. Mở terminal trong Docker Desktop
2. Chạy lệnh:
   ```bash
   cd D:\QLTS\QLTSC\qlts-new8
   docker-compose build --no-cache
   docker-compose up -d
   ```

**Cách 2: Xóa và build lại**
1. Dừng containers: Click **Stop** trên tất cả containers
2. Xóa containers: Click **Delete** trên tất cả containers
3. Vào tab **Images**
4. Tìm image `qlts-new8-web` (hoặc tên tương tự)
5. Xóa image: Click **Delete**
6. Quay lại terminal và chạy:
   ```bash
   docker-compose up --build
   ```

## Backup Database

```bash
# Backup PostgreSQL
docker-compose exec db pg_dump -U qlts_user qlts_db > backup.sql

# Restore
docker-compose exec -T db psql -U qlts_user qlts_db < backup.sql
```

