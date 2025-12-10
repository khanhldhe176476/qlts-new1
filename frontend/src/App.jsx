import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { App as AntApp } from 'antd'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import AssetList from './pages/Assets/List'
import AssetAdd from './pages/Assets/Add'
import AssetEdit from './pages/Assets/Edit'
import AssetTypeList from './pages/AssetTypes/List'
import UserList from './pages/Users/List'
import MaintenanceList from './pages/Maintenance/List'
import TransferList from './pages/Transfer/List'
import TrashList from './pages/Trash/List'
import InventoryBusinessDocPage from './pages/Inventory/BusinessDoc'
import { useAuthStore } from './stores/authStore'

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <AntApp>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <Layout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/assets" element={<AssetList />} />
                    <Route path="/assets/add" element={<AssetAdd />} />
                    <Route path="/assets/edit/:id" element={<AssetEdit />} />
                    <Route path="/asset-types" element={<AssetTypeList />} />
                    <Route path="/users" element={<UserList />} />
                    <Route path="/maintenance" element={<MaintenanceList />} />
                    <Route path="/transfer" element={<TransferList />} />
                    <Route path="/trash" element={<TrashList />} />
                    <Route path="/inventory/docs" element={<InventoryBusinessDocPage />} />
                  </Routes>
                </Layout>
              </PrivateRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AntApp>
  )
}

export default App


