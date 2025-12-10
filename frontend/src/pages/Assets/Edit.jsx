import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Form, Input, InputNumber, Select, Button, Card, Space, DatePicker, message } from 'antd'
import { assetService } from '../../services/assets'
import { assetTypeService } from '../../services/assetTypes'
import dayjs from 'dayjs'

export default function AssetEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [assetTypes, setAssetTypes] = useState([])
  const [loading, setLoading] = useState(false)
  const [dataLoading, setDataLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [assetResponse, typesResponse] = await Promise.all([
          assetService.getById(id),
          assetTypeService.getAll(),
        ])
        setAssetTypes(typesResponse || [])
        if (assetResponse) {
          form.setFieldsValue({
            ...assetResponse,
            purchase_date: assetResponse.purchase_date ? dayjs(assetResponse.purchase_date) : null,
          })
        }
      } catch (error) {
        message.error('Không thể tải dữ liệu')
        navigate('/assets')
      } finally {
        setDataLoading(false)
      }
    }
    fetchData()
  }, [id])

  const onFinish = async (values) => {
    setLoading(true)
    try {
      const data = {
        ...values,
        purchase_date: values.purchase_date ? values.purchase_date.format('YYYY-MM-DD') : null,
      }
      await assetService.update(id, data)
      message.success('Cập nhật tài sản thành công')
      navigate('/assets')
    } catch (error) {
      message.error('Cập nhật tài sản thất bại')
    } finally {
      setLoading(false)
    }
  }

  if (dataLoading) {
    return <Card title="Đang tải...">Loading...</Card>
  }

  return (
    <Card title={`Chỉnh sửa tài sản #${id}`}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Form.Item label="Tên tài sản" name="name" rules={[{ required: true, message: 'Vui lòng nhập tên tài sản' }]}>
          <Input placeholder="Nhập tên tài sản" />
        </Form.Item>
        <Form.Item label="Loại tài sản" name="asset_type_id" rules={[{ required: true, message: 'Vui lòng chọn loại tài sản' }]}>
          <Select placeholder="Chọn loại tài sản">
            {assetTypes.map((type) => (
              <Select.Option key={type.id} value={type.id}>
                {type.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item label="Giá" name="price" rules={[{ required: true, message: 'Vui lòng nhập giá' }]}>
          <InputNumber style={{ width: '100%' }} min={0} placeholder="Nhập giá" />
        </Form.Item>
        <Form.Item label="Số lượng" name="quantity">
          <InputNumber min={1} />
        </Form.Item>
        <Form.Item label="Ngày mua" name="purchase_date">
          <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
        </Form.Item>
        <Form.Item label="Mã thiết bị" name="device_code">
          <Input placeholder="Nhập mã thiết bị" />
        </Form.Item>
        <Form.Item label="Tình trạng" name="condition_label">
          <Select placeholder="Chọn tình trạng">
            <Select.Option value="Mới">Mới</Select.Option>
            <Select.Option value="Còn tốt">Còn tốt</Select.Option>
            <Select.Option value="Đã sử dụng">Đã sử dụng</Select.Option>
            <Select.Option value="Cần kiểm tra">Cần kiểm tra</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="Trạng thái" name="status">
          <Select>
            <Select.Option value="active">Đang sử dụng</Select.Option>
            <Select.Option value="maintenance">Bảo trì</Select.Option>
            <Select.Option value="disposed">Đã thanh lý</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="Ghi chú" name="notes">
          <Input.TextArea rows={4} placeholder="Nhập ghi chú" />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>Lưu</Button>
            <Button onClick={() => navigate('/assets')}>Hủy</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}

