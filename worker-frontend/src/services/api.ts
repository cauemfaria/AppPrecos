import axios from 'axios';
import type { Market, SaveScanResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://appprecos.onrender.com/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

api.interceptors.response.use(
  response => response,
  error => {
    if (!error.response) {
      (error as any).isBackendDown = true;
    }
    return Promise.reject(error);
  }
);

export const marketService = {
  getMarkets: async (): Promise<Market[]> => {
    const response = await api.get<Market[]>('/markets');
    return response.data;
  },
};

export const scanService = {
  saveScan: async (data: {
    market_id: string;
    ean: string;
    varejo_price: number;
    atacado_price?: number;
  }): Promise<SaveScanResponse> => {
    const response = await api.post<SaveScanResponse>('/scan/save', data);
    return response.data;
  },
};

export default api;
