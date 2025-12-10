import React from 'react'
import { Typography } from 'antd'

const { Title, Paragraph } = Typography

/**
 * Tài liệu nghiệp vụ: Kiểm kê tài sản
 *
 * Component thuần hiển thị, dễ tái sử dụng cho các màn tài liệu khác.
 */
export default function BusinessDocInventory() {
  return (
    <div
      style={{
        background: '#fff',
        padding: 24,
        borderRadius: 8,
        border: '1px solid #f0f0f0',
        maxWidth: 900,
      }}
    >
      <Typography>
        <Title level={3} style={{ marginTop: 0 }}>
          Tài liệu nghiệp vụ - Kiểm kê tài sản
        </Title>

        <Title level={4} style={{ marginTop: 24 }}>
          1. Mục tiêu kiểm kê
        </Title>
        <ul style={{ paddingLeft: 24, marginBottom: 0 }}>
          <li>
            <Paragraph style={{ marginBottom: 8 }}>
              Xác nhận thực tế từng tài sản do phường quản lý.
            </Paragraph>
          </li>
          <li>
            <Paragraph style={{ marginBottom: 8 }}>
              Đối chiếu với sổ/phần mềm để phát hiện thừa, thiếu, hư hỏng, sai thông tin.
            </Paragraph>
          </li>
          <li>
            <Paragraph style={{ marginBottom: 8 }}>
              Là căn cứ pháp lý cho: chốt sổ năm, tính hao mòn, ghi tăng/giảm, thanh lý hoặc điều chuyển.
            </Paragraph>
          </li>
        </ul>

        <Title level={4} style={{ marginTop: 24 }}>
          2. Nguyên tắc kiểm kê
        </Title>
        <ul style={{ paddingLeft: 24 }}>
          <li>
            <Paragraph style={{ marginBottom: 8 }}>
              Kiểm kê theo đúng thời điểm chốt kiểm kê.
            </Paragraph>
          </li>
          <li>
            <Paragraph style={{ marginBottom: 8 }}>
              Mọi chênh lệch phải ghi rõ: <strong>nguyên nhân – hướng xử lý – thẩm quyền phê duyệt</strong>.
            </Paragraph>
          </li>
          <li>
            <Paragraph style={{ marginBottom: 0 }}>
              Tài sản hỏng nặng chỉ ghi giảm khi có <strong>Quyết định thanh lý</strong>.
            </Paragraph>
          </li>
        </ul>
      </Typography>
    </div>
  )
}




















