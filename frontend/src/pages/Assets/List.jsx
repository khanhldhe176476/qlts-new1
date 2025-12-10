import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Space, Tag, Popconfirm, message, Select, Upload } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { assetService } from '../../services/assets'
import { assetTypeService } from '../../services/assetTypes'

export default function AssetList() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [assetTypes, setAssetTypes] = useState([])
  const [searchText, setSearchText] = useState('')
  const [selectedType, setSelectedType] = useState(null)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  })
  const navigate = useNavigate()

  const fetchAssetTypes = async () => {
    try {
      const response = await assetTypeService.getAll()
      setAssetTypes(response || [])
    } catch (error) {
      console.error('Failed to load asset types', error)
    }
  }

  const fetchData = async (page = 1, search = '', assetTypeId = null) => {
    setLoading(true)
    try {
      const params = {
        page,
        per_page: pagination.pageSize,
      }
      if (search) params.search = search
      if (assetTypeId) params.asset_type_id = assetTypeId
      
      const response = await assetService.getAll(params)
      setData(response.items || response || [])
      setPagination({
        ...pagination,
        current: page,
        total: response.total || (response.items ? response.items.length : 0),
      })
    } catch (error) {
      message.error('Không thể tải dữ liệu')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAssetTypes()
    fetchData()
  }, [])

  const columns = [
    {
      title: 'STT',
      key: 'index',
      width: 80,
      render: (_, __, index) => (pagination.current - 1) * pagination.pageSize + index + 1,
    },
    {
      title: 'Tên tài sản',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Loại tài sản',
      dataIndex: ['asset_type', 'name'],
      key: 'asset_type',
    },
    {
      title: 'Giá',
      dataIndex: 'price',
      key: 'price',
      render: (price) => price?.toLocaleString('vi-VN'),
    },
    {
      title: 'Số lượng',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colors = {
          active: 'green',
          maintenance: 'orange',
          disposed: 'red',
        }
        const labels = {
          active: 'Đang sử dụng',
          maintenance: 'Bảo trì',
          disposed: 'Đã thanh lý',
        }
        return (
          <Tag color={colors[status]} style={{ whiteSpace: 'nowrap' }}>
            {labels[status] || status}
          </Tag>
        )
      },
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            icon={<EditOutlined />}
            size="small"
            onClick={() => navigate(`/assets/edit/${record.id}`)}
          />
          <Popconfirm
            title="Xóa tài sản này?"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button
              danger
              icon={<DeleteOutlined />}
              size="small"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const handleDelete = async (id) => {
    try {
      await assetService.delete(id)
      message.success('Xóa thành công')
      fetchData(pagination.current, searchText, selectedType)
    } catch (error) {
      message.error('Xóa thất bại')
    }
  }

  const handleSearch = (value) => {
    setSearchText(value)
    fetchData(1, value, selectedType)
  }

  const handleTypeFilter = (value) => {
    setSelectedType(value)
    fetchData(1, searchText, value)
  }

  const handleExport = async () => {
    try {
      const blob = await assetService.export({ asset_type_id: selectedType, search: searchText })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tai_san_${new Date().toISOString().split('T')[0]}.xlsx`
      a.click()
      message.success('Xuất file thành công')
    } catch (error) {
      message.error('Xuất file thất bại')
    }
  }

  const handleImport = async (file) => {
    try {
      await assetService.import(file)
      message.success('Import thành công')
      fetchData(pagination.current, searchText, selectedType)
    } catch (error) {
      message.error('Import thất bại')
    }
    return false
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <Space wrap>
          <Input
            placeholder="Tìm kiếm tài sản..."
            prefix={<SearchOutlined />}
            style={{ width: 300 }}
            allowClear
            onPressEnter={(e) => handleSearch(e.target.value)}
            onChange={(e) => !e.target.value && handleSearch('')}
          />
          <Select
            placeholder="Tất cả loại"
            style={{ width: 200 }}
            allowClear
            onChange={handleTypeFilter}
            value={selectedType}
          >
            {assetTypes.map((type) => (
              <Select.Option key={type.id} value={type.id}>
                {type.name}
              </Select.Option>
            ))}
          </Select>
        </Space>
        <Space>
          <Upload
            beforeUpload={handleImport}
            showUploadList={false}
            accept=".xlsx,.xls"
          >
            <Button icon={<UploadOutlined />}>Import Excel</Button>
          </Upload>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            Xuất dữ liệu
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/assets/add')}
          >
            Thêm tài sản
          </Button>
        </Space>
      </div>
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="id"
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showTotal: (total) => `Tổng ${total} tài sản`,
          onChange: (page, pageSize) => {
            setPagination({ ...pagination, pageSize })
            fetchData(page, searchText, selectedType)
          },
        }}
      />
    </div>
  )
}

