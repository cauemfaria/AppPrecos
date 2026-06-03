import axios from 'axios';
import type { Market, SaveScanResponse } from '../types';
import { supabase, getSessionSafe } from '../lib/supabase';
import { useAuthStore } from '../store/useAuthStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://appprecos.onrender.com/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Attach JWT to every request. Uses getSessionSafe so a stalled auth lock can
// never hang an outgoing request before it even reaches the network.
api.interceptors.request.use(async (config) => {
  const session = await getSessionSafe();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// On 401, try token refresh then sign out
api.interceptors.response.use(
  response => response,
  async (error) => {
    if (error.response?.status === 401) {
      const { data: { session } } = await supabase.auth.refreshSession();
      if (session) {
        error.config.headers.Authorization = `Bearer ${session.access_token}`;
        return api(error.config);
      }
      await useAuthStore.getState().signOut();
    }
    return Promise.reject(error);
  }
);

// Global error interceptor for network failures (matches main frontend behavior).
api.interceptors.response.use(
  response => response,
  error => {
    if (!error.response) {
      const message = error.code === 'ECONNABORTED'
        ? 'Tempo esgotado - o servidor não está respondendo'
        : 'Servidor inacessível. Verifique sua conexão com a internet.';

      console.error('[API Error]', message, error.message);

      error.isBackendDown = true;
      error.backendErrorMessage = message;
    }
    return Promise.reject(error);
  }
);

/** Verifies the authenticated backend API is ready (same probe as market lists). */
export async function verifyBackendReady(): Promise<void> {
  await api.get<Market[]>('/markets', { timeout: 15_000 });
}

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
