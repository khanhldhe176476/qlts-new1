import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Space, Popconfirm, message, Modal, Form } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons'
import { assetTypeService } from '../../services/assetTypes'

export default function AssetTypeList() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await assetTypeService.getAll()
      let filtered = response || []
      if (searchText) {
        filtered = filtered.filter(item =>
          item.name.toLowerCase().includes(searchText.toLowerCase()) ||
          (item.description && item.description.toLowerCase().includes(searchText.toLowerCase()))
        )
      }
      setData(filtered)
    } catch (error) {
      message.error('Không thể tải dữ liệu')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [searchText])

  const columns = [
    {
      title: 'STT',
      key: 'index',
      width: 80,
      render: (_, __, index) => index + 1,
    },
    {
      title: 'Tên loại tài sản',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Mô tả',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Số tài sản',
      dataIndex: 'asset_count',
      key: 'asset_count',
      render: (count) => count || 0,
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
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Xóa loại tài sản này?"
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
      await assetTypeService.delete(id)
      message.success('Xóa thành công')
      fetchData()
    } catch (error) {
      message.error('Xóa thất bại')
    }
  }

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record) => {
    setEditingItem(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleSubmit = async (values) => {
    try {
      if (editingItem) {
        await assetTypeService.update(editingItem.id, values)
        message.success('Cập nhật thành công')
      } else {
        await assetTypeService.create(values)
        message.success('Thêm thành công')
      }
      setModalVisible(false)
      fetchData()
    } catch (error) {
      message.error(editingItem ? 'Cập nhật thất bại' : 'Thêm thất bại')
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Input
          placeholder="Tìm kiếm loại tài sản..."
          prefix={<SearchOutlined />}
          style={{ width: 300 }}
          allowClear
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          Thêm loại tài sản
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="id"
        pagination={{
          showTotal: (total) => `Tổng ${total} loại tài sản`,
        }}
      />
      <Modal
        title={editingItem ? 'Chỉnh sửa loại tài sản' : 'Thêm loại tài sản mới'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="Tên loại tài sản"
            rules={[{ required: true, message: 'Vui lòng nhập tên loại tài sản' }]}
          >
            <Input placeholder="Nhập tên loại tài sản" />
          </Form.Item>
          <Form.Item
            name="description"
            label="Mô tả"
          >
            <Input.TextArea rows={4} placeholder="Nhập mô tả" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingItem ? 'Cập nhật' : 'Thêm'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>Hủy</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

