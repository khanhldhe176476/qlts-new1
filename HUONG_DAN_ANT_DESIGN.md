# Hướng dẫn nâng cấp UI với Ant Design

## Tổng quan

Hệ thống đã được nâng cấp với React + Ant Design frontend. Frontend mới sẽ thay thế giao diện AdminLTE cũ.

## Cài đặt

### 1. Cài đặt Node.js và npm

Đảm bảo bạn đã cài đặt Node.js (phiên bản 16 trở lên):
- Tải từ: https://nodejs.org/
- Hoặc dùng: `choco install nodejs` (Windows với Chocolatey)

### 2. Cài đặt dependencies

```bash
cd frontend
npm install
```

### 3. Chạy development server

```bash
npm run dev
```

Frontend sẽ chạy tại: http://localhost:3000

### 4. Build cho production

```bash
npm run build
```

Sau khi build, files sẽ được tạo trong `static/frontend/`

## Cấu trúc Frontend

```
frontend/
├── src/
│   ├── components/      # Components dùng chung
│   │   └── Layout.jsx   # Layout chính với Ant Design
│   ├── pages/           # Các trang
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Assets/
│   │   ├── AssetTypes/
│   │   ├── Users/
│   │   ├── Maintenance/
│   │   ├── Transfer/
│   │   └── Trash/
│   ├── services/        # API services
│   │   └── api.js
│   ├── stores/          # State management (Zustand)
│   │   └── authStore.js
│   ├── App.jsx          # App component
│   └── main.jsx         # Entry point
├── package.json
└── vite.config.js
```

## Tích hợp với Flask

### Option 1: Chạy riêng biệt (Development)

- Frontend: http://localhost:3000 (Vite dev server)
- Backend: http://localhost:5000 (Flask API)

Vite đã được cấu hình để proxy `/api/*` đến Flask.

### Option 2: Serve từ Flask (Production)

1. Build frontend: `npm run build`
2. Cập nhật Flask để serve static files từ `static/frontend/`
3. Thêm route để serve React app:

```python
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path and os.path.exists(os.path.join(app.static_folder, 'frontend', path)):
        return send_from_directory(os.path.join(app.static_folder, 'frontend'), path)
    return send_from_directory(os.path.join(app.static_folder, 'frontend'), 'index.html')
```

## Tính năng mới

### UI Components với Ant Design

- **Layout**: Sidebar navigation với Ant Design Layout
- **Tables**: Data tables với sorting, filtering, pagination
- **Forms**: Form components với validation
- **Modals**: Dialog và confirm dialogs
- **Notifications**: Message và notification system
- **Icons**: Ant Design Icons

### Responsive Design

- Mobile-friendly
- Tablet support
- Desktop optimized

### Dark Mode (Có thể thêm sau)

Ant Design hỗ trợ theme customization, có thể thêm dark mode.

## API Integration

Frontend sử dụng axios để gọi API. Tất cả API calls đều qua `/api/*` endpoint.

Cần đảm bảo Flask API routes có prefix `/api` hoặc cấu hình proxy đúng.

## Troubleshooting

### Lỗi: Cannot find module

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Lỗi: Port already in use

Thay đổi port trong `vite.config.js`:
```js
server: {
  port: 3001, // Thay đổi port
}
```

### Lỗi: API không kết nối được

Kiểm tra:
1. Flask đang chạy tại port 5000
2. Proxy config trong `vite.config.js` đúng
3. CORS được enable trong Flask (nếu cần)

## Next Steps

1. Hoàn thiện các trang còn lại
2. Thêm form validation
3. Thêm error handling tốt hơn
4. Thêm loading states
5. Thêm unit tests
6. Optimize bundle size

















