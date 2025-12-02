# API Documentation

## Tổng quan

Hệ thống API RESTful cho Quản lý Tài sản với JWT Authentication và Swagger Documentation.

### Base URL
```
http://localhost:5000/api/v1
```

### Swagger UI
```
http://localhost:5000/api/v1/docs/
```

## Authentication

API sử dụng JWT (JSON Web Token) để xác thực. Để sử dụng API, bạn cần:

1. **Đăng nhập** để nhận access token
2. **Gửi token** trong header mỗi request: `Authorization: Bearer <token>`

### Endpoints

#### 1. Đăng nhập
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

#### 2. Làm mới Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

#### 3. Lấy thông tin User hiện tại
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

## Assets API

### List Assets
```http
GET /api/v1/assets?page=1&per_page=20&status=active&asset_type_id=1&search=laptop
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (int): Trang hiện tại (mặc định: 1)
- `per_page` (int): Số items mỗi trang (mặc định: 20)
- `status` (string): Lọc theo status (active, maintenance, disposed)
- `asset_type_id` (int): Lọc theo loại tài sản
- `search` (string): Tìm kiếm theo tên hoặc device_code

### Get Asset by ID
```http
GET /api/v1/assets/{id}
Authorization: Bearer <access_token>
```

### Create Asset
```http
POST /api/v1/assets
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Laptop Dell XPS 15",
  "price": 25000000,
  "quantity": 1,
  "status": "active",
  "asset_type_id": 1,
  "purchase_date": "2024-01-15",
  "device_code": "LAP001",
  "condition_label": "Mới",
  "warranty_start_date": "2024-01-15",
  "warranty_end_date": "2027-01-15",
  "warranty_period_months": 36
}
```

### Update Asset
```http
PUT /api/v1/assets/{id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Laptop Dell XPS 15 Updated",
  "status": "maintenance"
}
```

### Delete Asset
```http
DELETE /api/v1/assets/{id}
Authorization: Bearer <access_token>
```

## Users API (Admin only)

### List Users
```http
GET /api/v1/users?page=1&per_page=20&role_id=1&is_active=true&search=admin
Authorization: Bearer <access_token>
```

### Get User by ID
```http
GET /api/v1/users/{id}
Authorization: Bearer <access_token>
```

### Create User
```http
POST /api/v1/users
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "role_id": 2,
  "is_active": true,
  "asset_quota": 10
}
```

### Update User
```http
PUT /api/v1/users/{id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "email": "updated@example.com",
  "is_active": false
}
```

### Delete User
```http
DELETE /api/v1/users/{id}
Authorization: Bearer <access_token>
```

## Maintenance Records API

### List Maintenance Records
```http
GET /api/v1/maintenance?page=1&per_page=20&asset_id=1&status=completed&type=maintenance&date_from=2024-01-01&date_to=2024-12-31
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (int): Trang hiện tại
- `per_page` (int): Số items mỗi trang
- `asset_id` (int): Lọc theo asset ID
- `status` (string): Lọc theo status (completed, scheduled, in_progress, cancelled)
- `type` (string): Lọc theo type (maintenance, repair, inspection)
- `date_from` (string): Ngày bắt đầu (YYYY-MM-DD)
- `date_to` (string): Ngày kết thúc (YYYY-MM-DD)

### Get Maintenance Record by ID
```http
GET /api/v1/maintenance/{id}
Authorization: Bearer <access_token>
```

### Create Maintenance Record
```http
POST /api/v1/maintenance
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "asset_id": 1,
  "maintenance_date": "2024-01-15",
  "type": "maintenance",
  "description": "Bảo trì định kỳ",
  "vendor": "Công ty ABC",
  "person_in_charge": "Nguyễn Văn A",
  "cost": 500000,
  "next_due_date": "2024-07-15",
  "status": "completed"
}
```

### Update Maintenance Record
```http
PUT /api/v1/maintenance/{id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "in_progress",
  "cost": 600000
}
```

### Delete Maintenance Record
```http
DELETE /api/v1/maintenance/{id}
Authorization: Bearer <access_token>
```

## Asset Types API

### List Asset Types
```http
GET /api/v1/asset-types
Authorization: Bearer <access_token>
```

### Get Asset Type by ID
```http
GET /api/v1/asset-types/{id}
Authorization: Bearer <access_token>
```

### Create Asset Type (Admin only)
```http
POST /api/v1/asset-types
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Laptop",
  "description": "Máy tính xách tay"
}
```

### Update Asset Type (Admin only)
```http
PUT /api/v1/asset-types/{id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Laptop Updated",
  "description": "Mô tả cập nhật"
}
```

### Delete Asset Type (Admin only)
```http
DELETE /api/v1/asset-types/{id}
Authorization: Bearer <access_token>
```

## Error Responses

Tất cả các lỗi trả về với format:
```json
{
  "message": "Mô tả lỗi",
  "error": "error_code"
}
```

**HTTP Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Example với cURL

### Đăng nhập
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Lấy danh sách Assets
```bash
curl -X GET http://localhost:5000/api/v1/assets \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Tạo Asset mới
```bash
curl -X POST http://localhost:5000/api/v1/assets \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop Dell",
    "price": 20000000,
    "asset_type_id": 1,
    "status": "active"
  }'
```

## Example với Python requests

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"

# Đăng nhập
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
data = response.json()
access_token = data["access_token"]

# Sử dụng token
headers = {
    "Authorization": f"Bearer {access_token}"
}

# Lấy danh sách assets
assets_response = requests.get(f"{BASE_URL}/assets", headers=headers)
assets = assets_response.json()
print(assets)

# Tạo asset mới
new_asset = requests.post(f"{BASE_URL}/assets", headers=headers, json={
    "name": "Laptop Dell",
    "price": 20000000,
    "asset_type_id": 1,
    "status": "active"
})
print(new_asset.json())
```

## Swagger Documentation

Để xem tài liệu API đầy đủ với Swagger UI, truy cập:
```
http://localhost:5000/api/v1/docs/
```

Swagger UI cung cấp:
- Danh sách tất cả endpoints
- Thử nghiệm API trực tiếp
- Schema models
- Examples





