import { useInfiniteQuery, type QueryFunctionContext } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Car } from '../types';

interface CarsResponse {
  items: Car[];
  next_cursor: number | null;
  total: number;
}

const fetchCarsPage = async (
  context: QueryFunctionContext<readonly string[], number | null>
): Promise<CarsResponse> => {
  const { pageParam, queryKey } = context;
  const search = queryKey[1] || '';
  
  const { data } = await apiClient.get<CarsResponse>('/api/cars', {
    params: {
      cursor: pageParam,
      limit: 20,
      search: search || undefined,
    },
  });
  
  return data;
};

export const useCars = (search: string = '') => {
  return useInfiniteQuery({
    queryKey: ['cars', search] as const,
    queryFn: fetchCarsPage,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    initialPageParam: null as number | null,
  });
};
