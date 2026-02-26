import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ConfigProvider, Layout, Typography, Button, theme } from 'antd';
import { LogoutOutlined, CarOutlined } from '@ant-design/icons';
import { useAuthStore } from './store/useAuthStore';
import { LoginForm } from './features/auth/LoginForm';
import { CarsTable } from './components/CarsTable';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

function Dashboard() {
  const logout = useAuthStore((state) => state.logout);

  return (
    <Layout style={{ minHeight: '100vh', width: '100%' }}>
      <Header
        style={{
          background: '#fff',
          padding: '0 24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 1000,
          width: '100%',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <CarOutlined style={{ fontSize: 28, color: '#001529' }} />
          <div>
            <Title level={3} style={{ margin: 0, color: '#001529' }}>
              Auto Assistent
            </Title>
          </div>
        </div>

        <Button
          icon={<LogoutOutlined />}
          onClick={logout}
          size="large"
        >
          Logout
        </Button>
      </Header>

      <Content style={{ padding: '24px', width: '100%', background: '#f5f5f5' }}>
        <div style={{ maxWidth: 1600, margin: '0 auto', width: '100%' }}>
          <div style={{ marginBottom: 24 }}>
            <Title level={2} style={{ marginBottom: 8 }}>
              Car Listings
            </Title>
            <Text type="secondary" style={{ fontSize: 16 }}>
              Browse and manage all registered vehicles
            </Text>
          </div>

          <CarsTable />
        </div>
      </Content>
    </Layout>
  );
}

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#001529',
          borderRadius: 8,
        },
        algorithm: theme.defaultAlgorithm,
      }}
    >
      <QueryClientProvider client={queryClient}>
        {isAuthenticated ? <Dashboard /> : <LoginForm />}
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ConfigProvider>
  );
}

export default App;
