import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Alert } from 'antd'
import {
  AppstoreOutlined,
  UserOutlined,
  ToolOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import { assetService } from '../services/assets'
import { userService } from '../services/users'
import { maintenanceService } from '../services/maintenance'
import { transferService } from '../services/transfer'
import './Dashboard.css'

export default function Dashboard() {
  const [stats, setStats] = useState({
    assets: 0,
    users: 0,
    maintenance: 0,
    transfers: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    console.log('Dashboard: Component mounted, fetching stats...')
    const fetchStats = async () => {
      setLoading(true)
      setError(null)
      try {
        console.log('Dashboard: Starting API calls...')
        const [assetsRes, usersRes, maintenanceRes, transfersRes] = await Promise.all([
          assetService.getAll().catch((err) => {
            console.error('Dashboard: Error fetching assets:', err)
            return { total: 0, data: [] }
          }),
          userService.getAll().catch((err) => {
            console.error('Dashboard: Error fetching users:', err)
            return []
          }),
          maintenanceService.getAll().catch((err) => {
            console.error('Dashboard: Error fetching maintenance:', err)
            return []
          }),
          transferService.getAll().catch((err) => {
            console.error('Dashboard: Error fetching transfers:', err)
            return { total: 0, data: [] }
          }),
        ])
        
        console.log('Dashboard: API responses:', { assetsRes, usersRes, maintenanceRes, transfersRes })
        
        const newStats = {
          assets: assetsRes?.total || (Array.isArray(assetsRes) ? assetsRes.length : assetsRes?.data?.length || 0),
          users: Array.isArray(usersRes) ? usersRes.length : usersRes?.data?.length || 0,
          maintenance: Array.isArray(maintenanceRes) ? maintenanceRes.length : maintenanceRes?.data?.length || 0,
          transfers: transfersRes?.total || (Array.isArray(transfersRes) ? transfersRes.length : transfersRes?.data?.length || 0),
        }
        
        console.log('Dashboard: Setting stats:', newStats)
        setStats(newStats)
      } catch (error) {
        console.error('Dashboard: Failed to load stats', error)
        setError('Không thể tải dữ liệu thống kê. Vui lòng thử lại sau.')
      } finally {
        setLoading(false)
        console.log('Dashboard: Loading complete')
      }
    }
    fetchStats()
  }, [])

  const statCards = [
    {
      title: 'Tổng tài sản',
      value: stats.assets,
      icon: <AppstoreOutlined className="stat-icon stat-icon-blue" />,
      color: '#1890ff',
    },
    {
      title: 'Người dùng',
      value: stats.users,
      icon: <UserOutlined className="stat-icon stat-icon-green" />,
      color: '#52c41a',
    },
    {
      title: 'Bảo trì',
      value: stats.maintenance,
      icon: <ToolOutlined className="stat-icon stat-icon-orange" />,
      color: '#faad14',
    },
    {
      title: 'Bàn giao',
      value: stats.transfers,
      icon: <SwapOutlined className="stat-icon stat-icon-red" />,
      color: '#ff5200',
    },
  ]

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">Dashboard</h1>
      {error && (
        <Alert
          message="Lỗi tải dữ liệu"
          description={error}
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
      )}
      <Row gutter={[16, 16]}>
        {statCards.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card loading={loading} className="stat-card">
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={stat.icon}
                valueStyle={{ color: stat.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}

