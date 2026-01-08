# SƠ ĐỒ LUỒNG HỆ THỐNG QUẢN LÝ TÀI SẢN

## 1. SƠ ĐỒ TỔNG QUAN HỆ THỐNG

```
┌─────────────────────────────────────────────────────────────────┐
│                      HỆ THỐNG QLTS                              │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Web UI     │  │   Mobile UI   │  │   API Client  │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                  │                 │
│         └─────────────────┼──────────────────┘               │
│                           │                                    │
│                  ┌────────▼────────┐                          │
│                  │  Flask Server   │                          │
│                  │   (app.py)      │                          │
│                  └────────┬────────┘                          │
│                           │                                    │
│         ┌──────────────────┼──────────────────┐              │
│         │                  │                    │              │
│  ┌──────▼──────┐  ┌───────▼──────┐  ┌─────────▼──────┐      │
│  │  Web Routes │  │  API Routes  │  │  Blueprint      │      │
│  │  (app.py)  │  │ (routes_api) │  │  (new_site/)    │      │
│  └──────┬──────┘  └───────┬──────┘  └─────────┬──────┘      │
│         │                 │                    │              │
│         └─────────────────┼────────────────────┘              │
│                           │                                    │
│                  ┌────────▼────────┐                          │
│                  │  Business Logic │                          │
│                  │  - Auth         │                          │
│                  │  - Assets       │                          │
│                  │  - Maintenance  │                          │
│                  │  - Transfer     │                          │
│                  │  - Inventory    │                          │
│                  └────────┬────────┘                          │
│                           │                                    │
│                  ┌────────▼────────┐                          │
│                  │  Data Access    │                          │
│                  │  (SQLAlchemy)   │                          │
│                  └────────┬────────┘                          │
└───────────────────────────┼────────────────────────────────────┘
                            │
                  ┌─────────▼─────────┐
                  │   SQLite DB       │
                  │  (app.db)        │
                  └───────────────────┘
```

## 2. LUỒNG ĐĂNG NHẬP VÀ XÁC THỰC

```
┌──────────┐
│  User    │
└────┬─────┘
     │
     │ [1] Truy cập /login
     ▼
┌─────────────────┐
│  Login Page     │
│  - Username     │
│  - Password     │
└────┬────────────┘
     │
     │ [2] Submit form
     ▼
┌─────────────────┐
│  POST /login    │
│  - Verify creds │
└────┬────────────┘
     │
     ├─► [Invalid] ──► Hiển thị lỗi ──► Quay lại form
     │
     └─► [Valid]
         │
         │ [3] Tạo session
         ▼
┌─────────────────┐
│  Set Session    │
│  - user_id      │
│  - username     │
│  - role         │
└────┬────────────┘
     │
     │ [4] Update last_login
     ▼
┌─────────────────┐
│  Redirect       │
│  / (Dashboard)  │
└─────────────────┘
```

## 3. LUỒNG QUẢN LÝ TÀI SẢN - THÊM MỚI

```
┌──────────┐
│  Admin   │
└────┬─────┘
     │
     │ [1] GET /assets/add
     ▼
┌─────────────────┐
│  Load Form Data │
│  - Asset Types  │
│  - Users        │
└────┬────────────┘
     │
     │ [2] Hiển thị form
     ▼
┌─────────────────┐
│  Add Asset Form │
│  - Tên TS       │
│  - Loại TS      │
│  - Giá trị      │
│  - Số lượng     │
│  - Người dùng   │
│  - File upload  │
└────┬────────────┘
     │
     │ [3] POST /assets/add
     ▼
┌─────────────────┐
│  Validate Input │
│  - Required     │
│  - Format       │
│  - Unique name  │
└────┬────────────┘
     │
     ├─► [Invalid] ──► Hiển thị lỗi ──► Quay lại form
     │
     └─► [Valid]
         │
         │ [4] Upload file (nếu có)
         ▼
┌─────────────────┐
│  Save File      │
│  instance/      │
│  uploads/       │
└────┬────────────┘
     │
     │ [5] Tạo Asset record
     ▼
┌─────────────────┐
│  Create Asset   │
│  - Insert DB    │
│  - Link file    │
└────┬────────────┘
     │
     │ [6] Gán cho user (nếu có)
     ▼
┌─────────────────┐
│  Update         │
│  asset_user     │
│  (many-to-many) │
└────┬────────────┘
     │
     │ [7] Ghi audit log
     ▼
┌─────────────────┐
│  Create         │
│  AuditLog       │
│  (create action)│
└────┬────────────┘
     │
     │ [8] Commit transaction
     ▼
┌─────────────────┐
│  Success        │
│  Redirect       │
│  /assets        │
└─────────────────┘
```

## 4. LUỒNG BẢO TRÌ TÀI SẢN - WORKFLOW

```
┌─────────────────────────────────────────────────────────────┐
│              WORKFLOW BẢO TRÌ TÀI SẢN                        │
└─────────────────────────────────────────────────────────────┘

┌──────────┐
│  User   │
└────┬────┘
     │
     │ [1] Tạo yêu cầu bảo trì
     ▼
┌─────────────────┐
│  Create Request │
│  Status: created│
│  - Asset        │
│  - Type         │
│  - Description  │
│  - Priority     │
└────┬────────────┘
     │
     │ [2] Gửi phê duyệt
     ▼
┌─────────────────┐
│  Submit         │
│  Status:        │
│  pending        │
└────┬────────────┘
     │
     │ [3] Admin phê duyệt
     ▼
┌─────────────────┐
│  Approve        │
│  Status:        │
│  approved       │
│  - Assign to    │
│  - Set deadline │
└────┬────────────┘
     │
     │ [4] Bắt đầu thực hiện
     ▼
┌─────────────────┐
│  Start Work     │
│  Status:        │
│  in_progress    │
│  - Start time   │
└────┬────────────┘
     │
     │ [5] Ghi nhận chi phí/phụ tùng
     ▼
┌─────────────────┐
│  Record Costs   │
│  - Maintenance  │
│    Cost         │
│  - Parts        │
│  - Upload files │
└────┬────────────┘
     │
     │ [6] Hoàn thành
     ▼
┌─────────────────┐
│  Complete       │
│  Status:        │
│  completed      │
│  - End time     │
│  - Result       │
│  - Update asset │
│  - Set next due │
└─────────────────┘

     [Hoặc]
     
┌─────────────────┐
│  Failed         │
│  Status:        │
│  failed         │
│  - Reason       │
│  - Can retry    │
└─────────────────┘
```

## 5. LUỒNG ĐIỀU CHUYỂN TÀI SẢN

```
┌─────────────────────────────────────────────────────────────┐
│              ĐIỀU CHUYỂN TÀI SẢN                           │
└─────────────────────────────────────────────────────────────┘

┌──────────┐
│  Admin   │
└────┬─────┘
     │
     │ [1] Tạo yêu cầu điều chuyển
     ▼
┌─────────────────┐
│  Create Transfer │
│  - Asset         │
│  - From User     │
│  - To User       │
│  - Quantity      │
│  - Notes         │
└────┬────────────┘
     │
     │ [2] Generate code & token
     ▼
┌─────────────────┐
│  Save Transfer   │
│  - transfer_code│
│  - token         │
│  - expires_at    │
│  - status:       │
│    pending       │
└────┬────────────┘
     │
     │ [3] Gửi email xác nhận
     ▼
┌─────────────────┐
│  Send Email     │
│  To: to_user    │
│  - Link confirm │
│  - Transfer code│
│  - Asset info   │
└────┬────────────┘
     │
     │ [4] Người nhận nhận email
     ▼
┌─────────────────┐
│  Click Link     │
│  /transfer/     │
│  confirm/<code> │
└────┬────────────┘
     │
     │ [5] Verify token
     ▼
┌─────────────────┐
│  Check Token    │
│  - Valid?       │
│  - Expired?     │
│  - Status?      │
└────┬────────────┘
     │
     ├─► [Invalid/Expired] ──► Hiển thị lỗi
     │
     └─► [Valid]
         │
         │ [6] Hiển thị form xác nhận
         ▼
┌─────────────────┐
│  Confirm Form   │
│  - Asset info   │
│  - Quantity     │
│  - Confirm btn  │
└────┬────────────┘
     │
     │ [7] POST /transfer/confirm
     ▼
┌─────────────────┐
│  Confirm        │
│  - Update asset │
│  - Create       │
│    history      │
│  - Set status:  │
│    confirmed    │
└────┬────────────┘
     │
     │ [8] Success page
     ▼
┌─────────────────┐
│  Confirmed      │
│  Page           │
└─────────────────┘
```

## 6. LUỒNG KIỂM KÊ TÀI SẢN

```
┌─────────────────────────────────────────────────────────────┐
│              KIỂM KÊ TÀI SẢN                               │
└─────────────────────────────────────────────────────────────┘

┌──────────┐
│  Admin   │
└────┬─────┘
     │
     │ [1] Tạo phiếu kiểm kê
     ▼
┌─────────────────┐
│  Create         │
│  Inventory      │
│  Status: draft  │
│  - Code         │
│  - Name         │
│  - Date range   │
└────┬────────────┘
     │
     │ [2] Sinh dòng kiểm kê
     ▼
┌─────────────────┐
│  Generate Lines │
│  POST /api/     │
│  inventories/   │
│  <id>/generate- │
│  lines          │
│                 │
│  - Lấy tất cả TS│
│  - Tạo Result   │
│    cho mỗi TS   │
│  - Snapshot     │
│    book data    │
└────┬────────────┘
     │
     │ [3] Ghi nhận kết quả
     ▼
┌─────────────────┐
│  Record Result  │
│  POST /api/     │
│  inventories/   │
│  <id>/result    │
│                 │
│  For each asset:│
│  - actual_qty   │
│  - condition    │
│  - status       │
│  - notes        │
│  - photos       │
└────┬────────────┘
     │
     │ [4] Upload ảnh (nếu có)
     ▼
┌─────────────────┐
│  Save Photos    │
│  - Upload file  │
│  - Link to      │
│    result       │
└────┬────────────┘
     │
     │ [5] Gửi phê duyệt
     ▼
┌─────────────────┐
│  Submit         │
│  POST /api/     │
│  inventories/   │
│  <id>/submit    │
│                 │
│  Status:        │
│  pending        │
└────┬────────────┘
     │
     │ [6] Admin review
     ▼
┌─────────────────┐
│  Review         │
│  - Check results│
│  - Verify data  │
└────┬────────────┘
     │
     │ [7] Phê duyệt và khóa
     ▼
┌─────────────────┐
│  Approve & Lock │
│  POST /api/     │
│  inventories/   │
│  <id>/approve-  │
│  lock           │
│                 │
│  Status:        │
│  locked         │
│  - locked_at    │
│  - locked_by    │
└────┬────────────┘
     │
     │ [8] Đóng phiếu
     ▼
┌─────────────────┐
│  Close          │
│  POST /api/     │
│  inventories/   │
│  <id>/close     │
│                 │
│  Status:        │
│  closed         │
│  - closed_at    │
│  - closed_by    │
└─────────────────┘
```

## 7. LUỒNG GHI TĂNG/GIẢM TÀI SẢN

```
┌─────────────────────────────────────────────────────────────┐
│              GHI TĂNG/GIẢM TÀI SẢN                         │
└─────────────────────────────────────────────────────────────┘

┌──────────┐
│  Admin   │
└────┬─────┘
     │
     │ [1] Tạo chứng từ
     ▼
┌─────────────────┐
│  Create Voucher │
│  - Type:        │
│    increase/    │
│    decrease     │
│  - Date         │
│  - Description  │
└────┬────────────┘
     │
     │ [2] Thêm chi tiết
     ▼
┌─────────────────┐
│  Add Items      │
│  For each asset:│
│  - Asset        │
│  - Old value    │
│  - New value    │
│  - Quantity     │
│  - Reason       │
└────┬────────────┘
     │
     │ [3] Lưu chứng từ
     ▼
┌─────────────────┐
│  Save Voucher   │
│  - Generate code│
│  - Save items   │
└────┬────────────┘
     │
     │ [4] Cập nhật tài sản
     ▼
┌─────────────────┐
│  Update Assets  │
│  If increase:  │
│  - Add quantity │
│  - Update price │
│  If decrease:   │
│  - Reduce qty   │
│  - Update status│
└────┬────────────┘
     │
     │ [5] Ghi audit log
     ▼
┌─────────────────┐
│  Audit Log      │
│  - Voucher info │
│  - Changes      │
└─────────────────┘
```

## 8. LUỒNG KHẤU HAO TÀI SẢN

```
┌──────────┐
│  Admin   │
└────┬─────┘
     │
     │ [1] Chọn tài sản
     ▼
┌─────────────────┐
│  Select Asset   │
│  - Asset list   │
│  - Filter       │
└────┬────────────┘
     │
     │ [2] Tính khấu hao
     ▼
┌─────────────────┐
│  Calculate      │
│  Depreciation   │
│  - Method       │
│  - Period       │
│  - Rate         │
└────┬────────────┘
     │
     │ [3] Tạo bản ghi khấu hao
     ▼
┌─────────────────┐
│  Create         │
│  Depreciation   │
│  - Asset        │
│  - Period       │
│  - Amount       │
│  - Accumulated  │
└────┬────────────┘
     │
     │ [4] Cập nhật giá trị TS
     ▼
┌─────────────────┐
│  Update Asset   │
│  - Book value   │
│  - Depreciated  │
│    value        │
└────┬────────────┘
     │
     │ [5] Lưu vào DB
     ▼
┌─────────────────┐
│  Save           │
│  Depreciation   │
└─────────────────┘
```

## 9. LUỒNG BÁO CÁO

```
┌──────────┐
│  User    │
└────┬─────┘
     │
     │ [1] Chọn loại báo cáo
     ▼
┌─────────────────┐
│  Report Menu    │
│  - Dashboard    │
│  - Catalog      │
│  - TT144/TT23   │
│  - TT24         │
│  - TT35         │
│  - Special      │
└────┬────────────┘
     │
     │ [2] Chọn báo cáo
     ▼
┌─────────────────┐
│  Report Form    │
│  - Date range   │
│  - Filters      │
│  - Options      │
└────┬────────────┘
     │
     │ [3] Generate report
     ▼
┌─────────────────┐
│  Query Data     │
│  - Assets       │
│  - Maintenance  │
│  - Transfers    │
│  - Calculations │
└────┬────────────┘
     │
     │ [4] Format data
     ▼
┌─────────────────┐
│  Format Report  │
│  - Group        │
│  - Calculate    │
│  - Sort         │
└────┬────────────┘
     │
     │ [5] Render template
     ▼
┌─────────────────┐
│  Display Report │
│  - HTML view    │
└────┬────────────┘
     │
     │ [6] Export (optional)
     ▼
┌─────────────────┐
│  Export         │
│  - Excel        │
│  - PDF          │
└─────────────────┘
```

## 10. LUỒNG PHÂN QUYỀN

```
┌─────────────────────────────────────────────────────────────┐
│              PHÂN QUYỀN                                    │
└─────────────────────────────────────────────────────────────┘

┌──────────┐
│  Request │
└────┬─────┘
     │
     │ [1] User request
     ▼
┌─────────────────┐
│  Check Session  │
│  - user_id      │
│  - role         │
└────┬────────────┘
     │
     ├─► [No session] ──► Redirect /login
     │
     └─► [Has session]
         │
         │ [2] Check role
         ▼
┌─────────────────┐
│  Role Check     │
│  - Admin?       │
│  - Manager?     │
│  - User?        │
└────┬────────────┘
     │
     ├─► [Admin] ──► Allow all
     │
     └─► [Not Admin]
         │
         │ [3] Check permission
         ▼
┌─────────────────┐
│  Permission     │
│  Check          │
│  - Module       │
│  - Action       │
└────┬────────────┘
     │
     ├─► [No permission] ──► 403 Forbidden
     │
     └─► [Has permission]
         │
         │ [4] Allow access
         ▼
┌─────────────────┐
│  Execute        │
│  Action         │
└─────────────────┘
```

## 11. LUỒNG AUDIT LOG

```
┌──────────┐
│  Action  │
└────┬─────┘
     │
     │ [1] User performs action
     ▼
┌─────────────────┐
│  Action Handler │
│  - Create       │
│  - Update       │
│  - Delete       │
└────┬────────────┘
     │
     │ [2] Execute action
     ▼
┌─────────────────┐
│  Update DB      │
│  - Save changes │
└────┬────────────┘
     │
     │ [3] Create audit log
     ▼
┌─────────────────┐
│  AuditLog       │
│  - user_id      │
│  - module       │
│  - action       │
│  - entity_id    │
│  - details      │
│  - timestamp    │
└────┬────────────┘
     │
     │ [4] Save log
     ▼
┌─────────────────┐
│  Commit         │
│  Transaction    │
└─────────────────┘
```

## 12. SƠ ĐỒ QUAN HỆ DATABASE (ERD)

```
┌─────────────┐
│    Role     │
├─────────────┤
│ id (PK)     │
│ name        │
└──────┬──────┘
       │ 1:N
       │
┌──────▼──────┐      ┌──────────────┐      ┌──────────────┐
│    User     │      │  Permission  │      │UserPermission│
├─────────────┤      ├──────────────┤      ├──────────────┤
│ id (PK)     │      │ id (PK)      │      │ id (PK)     │
│ username    │      │ module       │      │ user_id (FK) │
│ password_   │      │ action       │      │ permission_ │
│   hash      │      │ name         │      │   id (FK)   │
│ email       │      └──────┬───────┘      │ granted     │
│ role_id (FK)│            │ N:M          └──────────────┘
│ is_active   │      ┌──────▼───────┐
└──────┬──────┘      │UserPermission│
       │             └──────────────┘
       │ 1:N
       │
┌──────▼──────┐      ┌──────────────┐
│   Asset     │      │  asset_user  │
├─────────────┤      ├──────────────┤
│ id (PK)     │◄────┤ asset_id (FK) │
│ name        │  N:M │ user_id (FK) │
│ price       │      └──────────────┘
│ asset_type_ │            │
│   id (FK)   │            │
│ user_id (FK)│            │
└──────┬──────┘      ┌──────▼──────┐
       │             │    User     │
       │ 1:N         └─────────────┘
       │
┌──────▼──────────┐
│MaintenanceRecord│
├─────────────────┤
│ id (PK)         │
│ asset_id (FK)   │
│ status          │
└─────────────────┘

┌─────────────┐
│ AssetType   │
├─────────────┤
│ id (PK)     │
│ name        │
└──────┬──────┘
       │ 1:N
       │
┌──────▼──────┐
│   Asset     │
└─────────────┘

┌─────────────┐
│ Inventory   │
├─────────────┤
│ id (PK)     │
│ code        │
│ status      │
└──────┬──────┘
       │ 1:N
       │
┌──────▼──────────┐
│InventoryResult  │
├─────────────────┤
│ id (PK)         │
│ inventory_id(FK)│
│ asset_id (FK)   │
│ actual_qty      │
└─────────────────┘

┌─────────────┐
│AssetTransfer│
├─────────────┤
│ id (PK)     │
│ asset_id(FK)│
│ from_user_  │
│   id (FK)   │
│ to_user_    │
│   id (FK)   │
│ status      │
└─────────────┘
```

## 13. LUỒNG XỬ LÝ LỖI

```
┌──────────┐
│  Request │
└────┬─────┘
     │
     │ [1] Process request
     ▼
┌─────────────────┐
│  Try Execute    │
│  Action         │
└────┬────────────┘
     │
     ├─► [Success] ──► Return result
     │
     └─► [Error]
         │
         │ [2] Catch exception
         ▼
┌─────────────────┐
│  Error Handler  │
│  - Log error     │
│  - Rollback DB   │
└────┬────────────┘
     │
     │ [3] Determine error type
     ▼
┌─────────────────┐
│  Error Type      │
│  - Validation    │
│  - Permission    │
│  - Not Found     │
│  - Server Error  │
└────┬────────────┘
     │
     │ [4] Return appropriate response
     ▼
┌─────────────────┐
│  Error Response │
│  - 400 Bad Req  │
│  - 401 Unauthor │
│  - 403 Forbidden│
│  - 404 Not Found│
│  - 500 Error    │
└─────────────────┘
```

---

**Lưu ý:** Các sơ đồ này có thể được sử dụng để:
1. Vẽ lại bằng công cụ như Draw.io, Lucidchart, hoặc Visio
2. Chuyển đổi sang định dạng Mermaid để hiển thị trong Markdown
3. Sử dụng làm tài liệu tham khảo khi phát triển hoặc bảo trì hệ thống




