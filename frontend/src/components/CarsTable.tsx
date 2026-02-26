import React, { useState, useMemo, useEffect } from 'react';
import { Table, List, Card, Input, Tag, Button, Space, Grid, Typography } from 'antd';
import { SearchOutlined, LinkOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useInView } from 'react-intersection-observer';
import { useCars } from '../hooks/useCars';
import type { Car } from '../types';

const { useBreakpoint } = Grid;
const { Text } = Typography;

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export const CarsTable: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearch = useDebounce(searchQuery, 500);
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    error,
  } = useCars(debouncedSearch);

  const { ref, inView } = useInView({
    threshold: 0,
  });

  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  const allCars = useMemo(() => {
    return data?.pages.flatMap((page) => page.items) ?? [];
  }, [data]);

  const totalCount = data?.pages[0]?.total ?? 0;

  const columns: ColumnsType<Car> = [
    {
      title: 'Brand',
      dataIndex: 'brand',
      key: 'brand',
      width: 120,
    },
    {
      title: 'Model',
      dataIndex: 'model',
      key: 'model',
      width: 180,
    },
    {
      title: 'Year',
      dataIndex: 'year',
      key: 'year',
      width: 100,
      align: 'center',
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      width: 150,
      render: (price: number) => (
        <strong>¥{price.toLocaleString()}</strong>
      ),
    },
    {
      title: 'Color',
      dataIndex: 'color',
      key: 'color',
      width: 120,
      render: (color: string) => (
        <Tag color="blue">{color}</Tag>
      ),
    },
    {
      title: 'Action',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Button
          type="link"
          icon={<LinkOutlined />}
          href={record.link}
          target="_blank"
          rel="noopener noreferrer"
        >
          View
        </Button>
      ),
    },
  ];

  if (error) {
    return (
      <Card>
        <p style={{ color: 'red' }}>Error loading cars: {(error as Error).message}</p>
      </Card>
    );
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%', display: 'flex' }}>
      {/* Search Input */}
      <div>
        <Input.Search
          size="large"
          placeholder="Search by brand, model, or color..."
          prefix={<SearchOutlined />}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          allowClear
          style={{ width: '100%', maxWidth: 600 }}
          loading={isLoading && debouncedSearch !== ''}
        />
        {totalCount > 0 && (
          <Text type="secondary" style={{ marginTop: 8, display: 'block' }}>
            {debouncedSearch ? `Found ${totalCount} results` : `Total: ${totalCount} cars`}
          </Text>
        )}
      </div>

      {/* Desktop Table View */}
      {!isMobile && (
        <Table
          columns={columns}
          dataSource={allCars}
          rowKey="id"
          loading={isLoading}
          pagination={false}
          scroll={{ x: 800 }}
        />
      )}

      {/* Mobile List View */}
      {isMobile && (
        <List
          loading={isLoading}
          dataSource={allCars}
          renderItem={(car) => (
            <List.Item key={car.id}>
              <Card style={{ width: '100%' }}>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ fontSize: 18 }}>
                      {car.brand} {car.model}
                    </strong>
                    <Tag color="blue">{car.color}</Tag>
                  </div>
                  <div style={{ color: '#666' }}>Year: {car.year}</div>
                  <div style={{ fontSize: 20, fontWeight: 'bold', color: '#001529' }}>
                    ¥{car.price.toLocaleString()}
                  </div>
                  <Button
                    type="primary"
                    icon={<LinkOutlined />}
                    href={car.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    block
                  >
                    View Listing
                  </Button>
                </Space>
              </Card>
            </List.Item>
          )}
        />
      )}

      {/* Infinite Scroll Trigger */}
      {hasNextPage && (
        <div ref={ref} style={{ textAlign: 'center', padding: '20px' }}>
          {isFetchingNextPage ? (
            <span>Loading more...</span>
          ) : (
            <span>Scroll to load more</span>
          )}
        </div>
      )}

      {!hasNextPage && allCars.length > 0 && (
        <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
          All cars loaded
        </div>
      )}

      {allCars.length === 0 && !isLoading && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Text type="secondary" style={{ fontSize: 16 }}>
            {debouncedSearch ? 'No cars found matching your search' : 'No cars available'}
          </Text>
        </div>
      )}
    </Space>
  );
};
