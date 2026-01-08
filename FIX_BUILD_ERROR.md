# 🔧 Sửa lỗi Build Docker - Thiếu zustand

## ❌ Lỗi gặp phải

```
[vite]: Rollup failed to resolve import "zustand" from "/app/frontend/src/stores/authStore.js"
```

## ✅ Đã sửa

Đã thêm `zustand` vào `frontend/package.json`. Bây giờ cần **rebuild Docker image** để áp dụng thay đổi.

## 🚀 Cách rebuild (BẮT BUỘC dùng --no-cache)

### Bước 1: Dừng và xóa containers cũ (nếu có)

```bash
docker compose down
```

### Bước 2: Xóa image cũ (nếu có)

```bash
docker rmi qlts-new8-web
```

Hoặc xóa tất cả images liên quan:
```bash
docker images | grep qlts
docker rmi <image-id>
```

### Bước 3: Rebuild với --no-cache (QUAN TRỌNG!)

```bash
docker compose build --no-cache
```

**Lưu ý:** Phải dùng `--no-cache` để Docker không dùng cache cũ!

### Bước 4: Chạy containers

```bash
docker compose up -d
```

## 🎯 Hoặc làm tất cả trong 1 lệnh

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## ⏱️ Thời gian build

- Lần đầu: 5-10 phút (tải images, cài dependencies)
- Lần sau: 3-5 phút (nếu không dùng --no-cache)

## ✅ Kiểm tra build thành công

Sau khi build, bạn sẽ thấy:
```
✓ 105+ modules transformed
✓ built in Xs
```

Và không còn lỗi về `zustand`.

## 🔍 Nếu vẫn lỗi

### Kiểm tra package.json đã có zustand chưa:

```bash
cat frontend/package.json | grep zustand
```

Phải thấy:
```json
"zustand": "^4.4.7"
```

### Xóa hoàn toàn và build lại:

```bash
# Dừng tất cả
docker compose down -v

# Xóa images
docker rmi $(docker images | grep qlts | awk '{print $3}')

# Build lại từ đầu
docker compose build --no-cache
docker compose up -d
```

## 📝 Giải thích

- **Docker cache**: Docker lưu cache từng layer để build nhanh hơn
- **Vấn đề**: Khi thay đổi `package.json`, Docker vẫn dùng cache cũ
- **Giải pháp**: Dùng `--no-cache` để build lại từ đầu

## 🎉 Sau khi build thành công

Truy cập: **http://localhost**



