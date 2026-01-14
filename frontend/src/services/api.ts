import axios from 'axios';
import { 
  Market, 
  MarketProductsResponse, 
  ProductSearchResponse, 
  CompareRequest, 
  CompareResponse, 
  NFCeRequest, 
  NFCeResponse, 
  NFCeStatusResponse 
} from '../types';

// In a real app, this would be an environment variable
const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
};

export default api;
