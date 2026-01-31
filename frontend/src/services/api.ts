import axios from 'axios';
import type { 
  Market, 
  MarketProductsResponse, 
  ProductSearchResponse, 
  CompareRequest, 
  CompareResponse, 
  NFCeRequest, 
  NFCeResponse, 
  NFCeStatusResponse 
} from '../types';

// Use environment variable for API base URL, fallback to existing one
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://appprecos.onrender.com/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Global error interceptor for network failures
api.interceptors.response.use(
  response => response,
  error => {
    // Handle network errors (backend unreachable)
    if (!error.response) {
      const message = error.code === 'ECONNABORTED' 
        ? 'Request timed out - backend is not responding'
        : 'Backend server is unreachable. Check your internet connection.';
      
      console.error('[API Error]', message, error.message);
      
      // Add custom error property for UI to detect backend down
      (error as any).isBackendDown = true;
      (error as any).backendErrorMessage = message;
    }
    
    return Promise.reject(error);
  }
);

export const marketService = {
  getMarkets: async () => {
    const response = await api.get<Market[]>('/markets');
    return response.data;
  },

  getMarketProducts: async (marketId: string) => {
    const response = await api.get<MarketProductsResponse>(`/markets/${marketId}/products`);
    return response.data;
  },
};

export const productService = {
  searchProducts: async (name: string, limit: number = 50) => {
    const response = await api.get<ProductSearchResponse>('/products/search', {
      params: { name, limit },
    });
    return response.data;
  },

  compareProducts: async (request: CompareRequest) => {
    const response = await api.post<CompareResponse>('/products/compare', request);
    return response.data;
  },
};

export const nfceService = {
  extractNFCe: async (request: NFCeRequest) => {
    const response = await api.post<NFCeResponse>('/nfce/extract', request);
    return response.data;
  },

  getNfceStatus: async (recordId: number) => {
    const response = await api.get<NFCeStatusResponse>(`/nfce/status/${recordId}`);
    return response.data;
  },

  getProcessingNfces: async () => {
    const response = await api.get<NFCeStatusResponse[]>('/nfce/processing');
    return response.data;
  },
};

export default api;
