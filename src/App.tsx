import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ConfigProvider, Layout, Menu, Avatar, Dropdown, theme } from 'antd';
import {
  DashboardOutlined,
  BookOutlined,
  MessageOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useAuthStore } from './store';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Course from './pages/Course';
import Lesson from './pages/Lesson';
import Exercise from './pages/Exercise';
import zhCN from 'antd/locale/zh_CN';

const { Header, Sider, Content } = Layout;

// 需要登录的路由
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

// 主布局组件
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = React.useState(false);
  const { user, logout } = useAuthStore();
  const location = useLocation();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '学习仪表盘',
    },
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: 'AI 对话',
    },
    {
      key: '/courses',
      icon: <BookOutlined />,
      label: '我的课程',
    },
  ];

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout();
        localStorage.removeItem('token');
      },
    },
  ];

  return (
    <Layout className="min-h-screen">
      <Sider trigger={null} collapsible collapsed={collapsed} theme="light" className="shadow-lg">
        <div className="h-16 flex items-center justify-center">
          <h1 className={`text-xl font-bold text-blue-600 ${collapsed ? 'text-lg' : ''}`}>
            {collapsed ? '🎓' : 'AI 学习系统'}
          </h1>
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => (window.location.href = key)}
        />
      </Sider>
      <Layout>
        <Header className="bg-white px-4 flex items-center justify-between shadow-sm">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            className="text-lg"
          />
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
              <Avatar icon={<UserOutlined />} src={user?.avatar} />
              {!collapsed && <span className="font-medium">{user?.username}</span>}
            </div>
          </Dropdown>
        </Header>
        <Content className="m-4 p-6 bg-white rounded-lg shadow-sm min-h-[calc(100vh-128px)]">
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

// 导入 Button（在 Layout 中使用）
import { Button } from 'antd';

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          {/* 公开路由 */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* 保护路由 */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Chat />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/courses"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <div className="p-6">
                    <h1 className="text-2xl font-bold mb-4">📚 我的课程</h1>
                    <p className="text-gray-500">课程列表开发中...</p>
                  </div>
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/course/:courseId"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Course />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/course/:courseId/lesson/:lessonId"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Lesson />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/course/:courseId/lesson/:lessonId/exercise"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Exercise />
                </MainLayout>
              </ProtectedRoute>
            }
          />

          {/* 默认重定向 */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
