import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message } from 'antd';
import { UserOutlined, LockOutlined, CarOutlined } from '@ant-design/icons';
import axios from 'axios';
import { useAuthStore } from '../../store/useAuthStore';

const { Title, Text } = Typography;
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const LoginForm: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const setToken = useAuthStore((state) => state.setToken);
  const [form] = Form.useForm();

  const handleSubmit = async (values: { username: string; password: string }) => {
    setIsLoading(true);

    try {
      // FastAPI OAuth2 expects URLSearchParams format
      const formData = new URLSearchParams();
      formData.append('username', values.username);
      formData.append('password', values.password);

      const response = await axios.post(`${API_BASE_URL}/api/login`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token } = response.data;
      setToken(access_token);
      message.success('Login successful!');
    } catch (err) {
      if (axios.isAxiosError(err)) {
        message.error(err.response?.data?.detail || 'Login failed. Please try again.');
      } else {
        message.error('An unexpected error occurred.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100vw',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '20px',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: 500,
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <CarOutlined style={{ fontSize: 48, color: '#001529', marginBottom: 16 }} />
          <Title level={2} style={{ margin: 0, color: '#001529' }}>
            Auto Assistent
          </Title>
          <Text type="secondary">Admin Dashboard</Text>
        </div>

        {/* Login Form */}
        <Form
          form={form}
          name="login"
          onFinish={handleSubmit}
          size="large"
          layout="vertical"
        >
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Please enter your username!' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Enter your username"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="Password"
            rules={[{ required: true, message: 'Please enter your password!' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Enter your password"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading}
              block
              size="large"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </Form.Item>
        </Form>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Protected by JWT authentication
          </Text>
        </div>
      </Card>
    </div>
  );
};
