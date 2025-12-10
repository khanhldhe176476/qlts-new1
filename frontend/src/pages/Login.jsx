import React from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { authService } from '../services/auth'
import api from '../services/api'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuthStore()

  const onFinish = async (values) => {
    try {
      const response = await authService.login(values.username, values.password)
      if (response.access_token) {
        // Lấy thông tin user
        const userResponse = await api.get('/v1/auth/me', {
          headers: { Authorization: `Bearer ${response.access_token}` },
        })
        login(userResponse, response.access_token)
        message.success('Đăng nhập thành công!')
        navigate('/')
      }
    } catch (error) {
      message.error(error.response?.data?.message || 'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.')
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        style={{
          width: 400,
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div
            style={{
              fontSize: 48,
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #ff5200 0%, #ff7a33 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: 8,
            }}
          >
            MH
          </div>
          <h2 style={{ margin: 0 }}>Quản lý tài sản công</h2>
          <p style={{ color: '#8c8c8c', marginTop: 8 }}>Đăng nhập vào hệ thống</p>
        </div>
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Vui lòng nhập tên đăng nhập!' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Tên đăng nhập"
            />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Vui lòng nhập mật khẩu!' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Mật khẩu"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              style={{
                background: 'linear-gradient(135deg, #ff5200 0%, #ff7a33 100%)',
                border: 'none',
                height: 40,
              }}
            >
              Đăng nhập
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

