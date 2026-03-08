export interface Market {
  id: number;
  market_id: string;
  name: string;
  address: string;
}

export interface ScanRecord {
  ean: string;
  varejo_price: number;
  atacado_price?: number;
  savedAt: number;
}

export interface SaveScanResponse {
  success: boolean;
  id: number;
}
