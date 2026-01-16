export interface Market {
  id: number;
  market_id: string;
  name: string;
  address: string;
}

export interface Product {
  id: number;
  market_id: string;
  ean: string;
  ncm: string;
  product_name: string;
  price: number;
  unidade_comercial: string;
  image_url?: string;
}

export interface MarketProductsResponse {
  market: Market;
  products: Product[];
  total: number;
}

export interface ProductSearchItem {
  product_name: string;
  ean: string;
  ncm: string;
  unidade_comercial: string;
  markets_count: number;
  min_price: number;
  max_price: number;
  image_url?: string;
}

export interface ProductSearchResponse {
  query: string;
  results: ProductSearchItem[];
  total: number;
}

export interface CompareRequestProduct {
  ean?: string;
  ncm?: string;
  product_name?: string;
}

export interface CompareRequest {
  products: CompareRequestProduct[];
  market_ids: string[];
}

export interface ComparisonProductRow {
  product_name: string;
  ean: string;
  ncm: string;
  image_url?: string | null;
  prices: Record<string, number | null>;
  min_price: number | null;
  max_price: number | null;
  all_equal: boolean;
}

export interface CompareResponse {
  markets: Record<string, string>;
  comparison: ComparisonProductRow[];
}

export interface NFCeRequest {
  url: string;
  save: boolean;
  async?: boolean;
}

export interface NFCeResponse {
  message: string;
  status: string;
  record_id?: number;
  market?: Market & { action: string };
  products?: any[];
  statistics?: {
    products_saved_to_main: number;
    market_action: string;
  };
}

export interface NFCeStatusResponse {
  record_id: number;
  status: 'processing' | 'extracting' | 'success' | 'error' | 'unknown';
  nfce_url?: string;
  market_id?: string;
  market_name?: string;
  products_count?: number;
  error_message?: string;
  processed_at: string;
}
