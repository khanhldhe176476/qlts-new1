import React, { useState, useEffect } from 'react'
import { Table, Button, Space, Tag, message, Select } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { transferService } from '../../services/transfer'
import dayjs from 'dayjs'

export default function TransferList() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const navigate = useNavigate()

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = statusFilter ? { status: statusFilter } : {}
      const response = await transferService.getAll(params)
      setData(response.items || response || [])
    } catch (error) {
      message.error('Không thể tải dữ liệu')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [statusFilter])

  const columns = [
    {
      title: 'Mã bàn giao',
      dataIndex: 'transfer_code',
      key: 'transfer_code',
    },
    {
      title: 'Tài sản',
      dataIndex: ['asset', 'name'],
      key: 'asset_name',
    },
    {
      title: 'Người gửi',
      dataIndex: ['from_user', 'username'],
      key: 'from_user',
    },
    {
      title: 'Người nhận',
      dataIndex: ['to_user', 'username'],
      key: 'to_user',
    },
    {
      title: 'Số lượng',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: 'Đã xác nhận',
      key: 'confirmed',
      render: (_, record) => `${record.confirmed_quantity || 0}/${record.expected_quantity || 0}`,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colors = {
          pending: 'orange',
          confirmed: 'green',
          rejected: 'red',
          cancelled: 'default',
        }
        const labels = {
          pending: 'Chờ xác nhận',
          confirmed: 'Đã xác nhận',
          rejected: 'Đã từ chối',
          cancelled: 'Đã hủy',
        }
        return <Tag color={colors[status]}>{labels[status] || status}</Tag>
      },
    },
    {
      title: 'Ngày tạo',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => date ? dayjs(date).format('DD/MM/YYYY HH:mm') : '-',
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Select
          placeholder="Tất cả trạng thái"
          style={{ width: 200 }}
          allowClear
          value={statusFilter}
          onChange={setStatusFilter}
        >
          <Select.Option value="pending">Chờ xác nhận</Select.Option>
          <Select.Option value="confirmed">Đã xác nhận</Select.Option>
          <Select.Option value="rejected">Đã từ chối</Select.Option>
          <Select.Option value="cancelled">Đã hủy</Select.Option>
        </Select>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/transfer/create')}>
          Tạo bàn giao mới
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="id"
        pagination={{
          showTotal: (total) => `Tổng ${total} bản ghi`,
        }}
      />
    </div>
  )
}
