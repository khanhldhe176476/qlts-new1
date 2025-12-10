import React, { useState, useEffect } from 'react'
import { Table, Tabs, Button, Space, message, Popconfirm } from 'antd'
import { RestoreOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../../services/api'
import dayjs from 'dayjs'

export default function TrashList() {
  const [activeTab, setActiveTab] = useState('all')
  const [assets, setAssets] = useState([])
  const [assetTypes, setAssetTypes] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchData = async (module) => {
    setLoading(true)
    try {
      const response = await api.get(`/trash?module=${module}`)
      if (module === 'all' || module === 'assets') {
        setAssets(response.assets || [])
      }
      if (module === 'all' || module === 'asset_type') {
        setAssetTypes(response.asset_types || [])
      }
      if (module === 'all' || module === 'users') {
        setUsers(response.users || [])
      }
    } catch (error) {
      message.error('Không thể tải dữ liệu')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(activeTab)
  }, [activeTab])

  const handleRestore = async (module, id) => {
    try {
      await api.post(`/trash/restore`, { module, id })
      message.success('Khôi phục thành công')
      fetchData(activeTab)
    } catch (error) {
      message.error('Khôi phục thất bại')
    }
  }

  const handlePermanentDelete = async (module, id) => {
    try {
      await api.post(`/trash/permanent-delete`, { module, id })
      message.success('Xóa vĩnh viễn thành công')
      fetchData(activeTab)
    } catch (error) {
      message.error('Xóa vĩnh viễn thất bại')
    }
  }

  const assetColumns = [
    { title: 'STT', key: 'index', render: (_, __, index) => index + 1 },
    { title: 'Tên', dataIndex: 'name', key: 'name' },
    { title: 'Loại', dataIndex: ['asset_type', 'name'], key: 'type' },
    { title: 'Giá', dataIndex: 'price', key: 'price', render: (price) => price?.toLocaleString('vi-VN') },
    {
      title: 'Ngày xóa',
      dataIndex: 'deleted_at',
      key: 'deleted_at',
      render: (date) => date ? dayjs(date).format('DD/MM/YYYY HH:mm') : '-',
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button icon={<RestoreOutlined />} size="small" onClick={() => handleRestore('asset', record.id)}>
            Khôi phục
          </Button>
          <Popconfirm
            title="Xóa vĩnh viễn?"
            onConfirm={() => handlePermanentDelete('asset', record.id)}
          >
            <Button danger icon={<DeleteOutlined />} size="small">Xóa</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const assetTypeColumns = [
    { title: 'STT', key: 'index', render: (_, __, index) => index + 1 },
    { title: 'Tên', dataIndex: 'name', key: 'name' },
    { title: 'Mô tả', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: 'Ngày xóa',
      dataIndex: 'deleted_at',
      key: 'deleted_at',
      render: (date) => date ? dayjs(date).format('DD/MM/YYYY HH:mm') : '-',
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button icon={<RestoreOutlined />} size="small" onClick={() => handleRestore('asset_type', record.id)}>
            Khôi phục
          </Button>
          <Popconfirm
            title="Xóa vĩnh viễn?"
            onConfirm={() => handlePermanentDelete('asset_type', record.id)}
          >
            <Button danger icon={<DeleteOutlined />} size="small">Xóa</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const userColumns = [
    { title: 'STT', key: 'index', render: (_, __, index) => index + 1 },
    { title: 'Username', dataIndex: 'username', key: 'username' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Vai trò', dataIndex: ['role', 'name'], key: 'role' },
    {
      title: 'Ngày xóa',
      dataIndex: 'deleted_at',
      key: 'deleted_at',
      render: (date) => date ? dayjs(date).format('DD/MM/YYYY HH:mm') : '-',
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button icon={<RestoreOutlined />} size="small" onClick={() => handleRestore('user', record.id)}>
            Khôi phục
          </Button>
          <Popconfirm
            title="Xóa vĩnh viễn?"
            onConfirm={() => handlePermanentDelete('user', record.id)}
          >
            <Button danger icon={<DeleteOutlined />} size="small">Xóa</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const tabItems = [
    {
      key: 'all',
      label: `Tất cả (${assets.length + assetTypes.length + users.length})`,
      children: (
        <>
          {assets.length > 0 && (
            <>
              <h3>Tài sản ({assets.length})</h3>
              <Table columns={assetColumns} dataSource={assets} rowKey="id" pagination={false} />
            </>
          )}
          {assetTypes.length > 0 && (
            <>
              <h3 style={{ marginTop: 24 }}>Loại tài sản ({assetTypes.length})</h3>
              <Table columns={assetTypeColumns} dataSource={assetTypes} rowKey="id" pagination={false} />
            </>
          )}
          {users.length > 0 && (
            <>
              <h3 style={{ marginTop: 24 }}>Người dùng ({users.length})</h3>
              <Table columns={userColumns} dataSource={users} rowKey="id" pagination={false} />
            </>
          )}
          {assets.length === 0 && assetTypes.length === 0 && users.length === 0 && (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <p>Thùng rác trống</p>
            </div>
          )}
        </>
      ),
    },
    {
      key: 'assets',
      label: `Tài sản (${assets.length})`,
      children: <Table columns={assetColumns} dataSource={assets} rowKey="id" loading={loading} />,
    },
    {
      key: 'asset_type',
      label: `Loại tài sản (${assetTypes.length})`,
      children: <Table columns={assetTypeColumns} dataSource={assetTypes} rowKey="id" loading={loading} />,
    },
    {
      key: 'users',
      label: `Người dùng (${users.length})`,
      children: <Table columns={userColumns} dataSource={users} rowKey="id" loading={loading} />,
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Thùng rác</h1>
      <Tabs activeKey={activeTab} items={tabItems} onChange={setActiveTab} />
    </div>
  )
}
