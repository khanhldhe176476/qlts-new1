# 🔍 Debug lỗi Build Docker - Rollup findVariable

## ❌ Lỗi gặp phải

```
at ModuleScope.findVariable
at Identifier.bind
```

Lỗi này thường do:
1. **Biến không được định nghĩa** trong scope
2. **Lỗi cú pháp JavaScript/JSX**
3. **Import/Export không đúng**
4. **Vấn đề với dependencies**

## 🔧 Cách debug

### Bước 1: Xem toàn bộ lỗi

Lỗi bạn gửi chỉ là stack trace. Cần xem **dòng lỗi đầu tiên** để biết file nào bị lỗi.

Trong terminal, tìm dòng có:
- `Error:` hoặc `SyntaxError:`
- Tên file (ví dụ: `BusinessDoc.jsx:12`)
- Thông báo lỗi cụ thể

### Bước 2: Kiểm tra file bị lỗi

Sau khi biết file nào, kiểm tra:
1. **Biến có được khai báo chưa?**
2. **Import có đúng không?**
3. **Có lỗi cú pháp không?** (dấu ngoặc, dấu phẩy, v.v.)

### Bước 3: Thử build local trước

Trước khi build Docker, thử build local:

```bash
cd frontend
npm install
npm run build
```

Nếu build local lỗi, sẽ dễ debug hơn.

## 🛠️ Các lỗi thường gặp

### 1. Biến không được khai báo

```jsx
// ❌ SAI
function Component() {
  return <div>{undefinedVariable}</div>
}

// ✅ ĐÚNG
function Component() {
  const variable = 'value'
  return <div>{variable}</div>
}
```

### 2. Import sai

```jsx
// ❌ SAI
import { Component } from './Component'  // Component không export default

// ✅ ĐÚNG
import Component from './Component'  // Component export default
```

### 3. Lỗi cú pháp JSX

```jsx
// ❌ SAI
return (
  <div>
    <Component />
  </div>  // Thiếu dấu ngoặc đóng
)

// ✅ ĐÚNG
return (
  <div>
    <Component />
  </div>
)
```

## 📝 Cách tìm file lỗi

1. **Xem toàn bộ output** trong terminal
2. Tìm dòng có `Error:` hoặc `SyntaxError:`
3. Dòng đó sẽ chỉ file và dòng số bị lỗi

Ví dụ:
```
Error: Identifier 'x' has already been declared
  at BusinessDoc.jsx:15:5
```

→ File `BusinessDoc.jsx`, dòng 15, cột 5

## 🚀 Giải pháp tạm thời

Nếu không tìm được file lỗi, thử:

1. **Xóa node_modules và rebuild:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

2. **Kiểm tra tất cả imports:**
```bash
# Tìm tất cả imports
grep -r "import.*from" frontend/src
```

3. **Kiểm tra syntax:**
```bash
# Nếu có ESLint
npm run lint
```

## 📋 Checklist

- [ ] Đã xem toàn bộ error message (không chỉ stack trace)
- [ ] Đã xác định được file bị lỗi
- [ ] Đã kiểm tra biến có được khai báo chưa
- [ ] Đã kiểm tra imports có đúng không
- [ ] Đã thử build local trước

## 💡 Gửi thông tin để debug

Nếu vẫn không tìm được, gửi:
1. **Toàn bộ error message** (từ đầu đến cuối)
2. **File và dòng số** bị lỗi (nếu có)
3. **Nội dung file** bị lỗi (nếu có)



