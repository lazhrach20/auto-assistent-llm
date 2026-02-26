export interface Car {
  id: number;
  brand: string;
  model: string;
  year: number;
  price: number;
  color: string;
  link: string;
}

export interface User {
  id: number;
  username: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface CarsListResponse {
  items: Car[];
  next_cursor: number | null;
  total: number;
}
