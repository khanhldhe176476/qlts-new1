# Sử dụng Python 3.11 (tương thích với Flask 2.3.3)
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các dependencies hệ thống (cần cho PostgreSQL và một số thư viện)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Tạo thư mục instance nếu chưa có (cho SQLite)
RUN mkdir -p instance/exports

# Expose port 5000 (internal, chỉ Nginx kết nối)
EXPOSE 5000

# Biến môi trường mặc định
ENV FLASK_APP=run.py
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=5000

# Chạy ứng dụng Flask (chạy trên 0.0.0.0 để Nginx có thể kết nối)
CMD ["python", "run.py"]
