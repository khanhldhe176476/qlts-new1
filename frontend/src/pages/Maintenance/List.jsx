import React, { useState, useEffect } from 'react'
import { Table, Button, Space, Tag, message, Modal, Form, DatePicker, Select, Input } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { maintenanceService } from '../../services/maintenance'
import { assetService } from '../../services/assets'
import dayjs from 'dayjs'

export default function MaintenanceList() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [assets, setAssets] = useState([])
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await maintenanceService.getAll()
      setData(response || [])
    } catch (error) {
      message.error('Không thể tải dữ liệu')
    } finally {
      setLoading(false)
    }
  }

  const fetchAssets = async () => {
    try {
      const response = await assetService.getAll()
      setAssets(response.items || response || [])
    } catch (error) {
      console.error('Failed to load assets', error)
    }
  }

  useEffect(() => {
    fetchData()
    fetchAssets()
  }, [])

  const columns = [
    {
      title: 'STT',
      key: 'index',
      width: 80,
      render: (_, __, index) => index + 1,
    },
    {
      title: 'Tài sản',
      dataIndex: ['asset', 'name'],
      key: 'asset_name',
    },
    {
      title: 'Ngày yêu cầu',
      dataIndex: 'request_date',
      key: 'request_date',
      render: (date) => date ? dayjs(date).format('DD/MM/YYYY') : '-',
    },
    {
      title: 'Loại bảo trì',
      dataIndex: 'maintenance_type',
      key: 'maintenance_type',
      render: (type) => {
        const colors = {
          preventive: 'blue',
          corrective: 'orange',
          emergency: 'red',
        }
        const labels = {
          preventive: 'Phòng ngừa',
          corrective: 'Sửa chữa',
          emergency: 'Khẩn cấp',
        }
        return <Tag color={colors[type]}>{labels[type] || type}</Tag>
      },
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colors = {
          pending: 'orange',
          in_progress: 'blue',
          completed: 'green',
          cancelled: 'red',
        }
        const labels = {
          pending: 'Chờ xử lý',
          in_progress: 'Đang xử lý',
          completed: 'Hoàn thành',
          cancelled: 'Đã hủy',
        }
        return <Tag color={colors[status]}>{labels[status] || status}</Tag>
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
            onClick={() => handleEdit(record)}
          />
          <Button
            danger
            icon={<DeleteOutlined />}
            size="small"
            onClick={() => handleDelete(record.id)}
          />
        </Space>
      ),
    },
  ]

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record) => {
    setEditingItem(record)
    form.setFieldsValue({
      ...record,
      request_date: record.request_date ? dayjs(record.request_date) : null,
      scheduled_date: record.scheduled_date ? dayjs(record.scheduled_date) : null,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await maintenanceService.delete(id)
      message.success('Xóa thành công')
      fetchData()
    } catch (error) {
      message.error('Xóa thất bại')
    }
  }

  const handleSubmit = async (values) => {
    try {
      const data = {
        ...values,
        request_date: values.request_date ? values.request_date.format('YYYY-MM-DD') : null,
        scheduled_date: values.scheduled_date ? values.scheduled_date.format('YYYY-MM-DD') : null,
      }
      if (editingItem) {
        await maintenanceService.update(editingItem.id, data)
        message.success('Cập nhật thành công')
      } else {
        await maintenanceService.create(data)
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
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          Thêm bảo trì
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
      <Modal
        title={editingItem ? 'Chỉnh sửa bảo trì' : 'Thêm bảo trì mới'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="asset_id"
            label="Tài sản"
            rules={[{ required: true, message: 'Vui lòng chọn tài sản' }]}
          >
            <Select placeholder="Chọn tài sản">
              {assets.map((asset) => (
                <Select.Option key={asset.id} value={asset.id}>
                  {asset.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="maintenance_type"
            label="Loại bảo trì"
            rules={[{ required: true, message: 'Vui lòng chọn loại bảo trì' }]}
          >
            <Select placeholder="Chọn loại bảo trì">
              <Select.Option value="preventive">Phòng ngừa</Select.Option>
              <Select.Option value="corrective">Sửa chữa</Select.Option>
              <Select.Option value="emergency">Khẩn cấp</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="request_date"
            label="Ngày yêu cầu"
            rules={[{ required: true, message: 'Vui lòng chọn ngày yêu cầu' }]}
          >
            <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
          </Form.Item>
          <Form.Item
            name="scheduled_date"
            label="Ngày dự kiến"
          >
            <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
          </Form.Item>
          <Form.Item
            name="status"
            label="Trạng thái"
          >
            <Select>
              <Select.Option value="pending">Chờ xử lý</Select.Option>
              <Select.Option value="in_progress">Đang xử lý</Select.Option>
              <Select.Option value="completed">Hoàn thành</Select.Option>
              <Select.Option value="cancelled">Đã hủy</Select.Option>
            </Select>
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
