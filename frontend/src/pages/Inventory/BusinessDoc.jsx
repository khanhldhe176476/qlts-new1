import React from 'react'
import { Typography, Card, Space } from 'antd'
import BusinessDocInventory from '../../components/BusinessDocInventory'

const { Title, Text } = Typography

export default function InventoryBusinessDocPage() {
  return (
    <div>
      <Space direction="vertical" size="middle" style={{ width: '100%', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>Kiểm kê tài sản</Title>
        <Text type="secondary">Tài liệu nghiệp vụ phục vụ công tác kiểm kê tài sản</Text>
      </Space>
      <Card>
        <BusinessDocInventory />
      </Card>
    </div>
  )
}




















