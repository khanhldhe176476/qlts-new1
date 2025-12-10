import React from 'react'
import { PageHeader } from '@ant-design/pro-layout'
import { Card } from 'antd'
import BusinessDocInventory from '../../components/BusinessDocInventory'

export default function InventoryBusinessDocPage() {
  return (
    <div>
      <PageHeader
        title="Kiểm kê tài sản"
        subTitle="Tài liệu nghiệp vụ phục vụ công tác kiểm kê tài sản"
      />
      <Card>
        <BusinessDocInventory />
      </Card>
    </div>
  )
}

















