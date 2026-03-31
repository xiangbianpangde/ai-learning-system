import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAuthStore } from '../store';

const { Title } = Typography;

const Login: React.FC = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const response = await authApi.login(values);
      login(response.user, response.token);
      localStorage.setItem('token', response.token);
      message.success('登录成功！');
      navigate('/dashboard');
    } catch (error: any) {
      message.error(error.response?.data?.message || '登录失败，请检查账号密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md shadow-xl">
        <div className="text-center mb-8">
          <Title level={2} className="!mb-2">🎓 AI 学习系统</Title>
          <Typography.Text type="secondary">欢迎回来，请登录您的账号</Typography.Text>
        </div>

        <Form name="login" onFinish={onFinish} layout="vertical" size="large">
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="邮箱" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              登录
            </Button>
          </Form.Item>

          <div className="text-center">
            <Typography.Text type="secondary">
              还没有账号？{' '}
              <Link to="/register" className="text-blue-500 hover:underline">
                立即注册
              </Link>
            </Typography.Text>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default Login;
