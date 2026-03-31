import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAuthStore } from '../store';

const { Title } = Typography;

const Register: React.FC = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username: string; email: string; password: string }) => {
    setLoading(true);
    try {
      const response = await authApi.register(values);
      login(response.user, response.token);
      localStorage.setItem('token', response.token);
      message.success('注册成功！');
      navigate('/dashboard');
    } catch (error: any) {
      message.error(error.response?.data?.message || '注册失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-teal-100">
      <Card className="w-full max-w-md shadow-xl">
        <div className="text-center mb-8">
          <Title level={2} className="!mb-2">🎓 创建账号</Title>
          <Typography.Text type="secondary">加入我们，开始 AI 辅助学习之旅</Typography.Text>
        </div>

        <Form name="register" onFinish={onFinish} layout="vertical" size="large">
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 2, message: '用户名至少 2 个字符' },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="邮箱" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少 6 个字符' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              注册
            </Button>
          </Form.Item>

          <div className="text-center">
            <Typography.Text type="secondary">
              已有账号？{' '}
              <Link to="/login" className="text-blue-500 hover:underline">
                立即登录
              </Link>
            </Typography.Text>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default Register;
