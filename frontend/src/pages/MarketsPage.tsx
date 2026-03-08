import React, { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { marketService, productService } from '../services/api';
import type { Market, Product, PriceHistoryItem } from '../types';
import { Store, Search, Package, MapPin, X, ArrowLeft, TrendingUp, Barcode } from 'lucide-react';

/* ─── helpers ─────────────────────────────────────────────── */

function timeAgo(dateStr?: string): string {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const days = Math.floor(diff / 86400000);
  if (days <= 0) return 'hoje';
  if (days === 1) return 'há 1 dia';
  if (days < 7) return `há ${days} dias`;
  const weeks = Math.floor(days / 7);
  if (weeks === 1) return 'há 1 semana';
  if (weeks < 5) return `há ${weeks} semanas`;
  const months = Math.floor(days / 30);
  if (months === 1) return 'há 1 mês';
  return `há ${months} meses`;
}

function fmtDate(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y.slice(2)}`;
}

/* ─── price chart tooltip ─────────────────────────────────── */

const PriceTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="px-3 py-2 rounded-xl text-xs font-semibold shadow-lg"
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        color: 'var(--color-text)',
      }}
    >
      <p style={{ color: 'var(--color-text-muted)' }}>{fmtDate(label)}</p>
      <p style={{ color: 'var(--color-cta)' }}>R$ {Number(payload[0].value).toFixed(2)}</p>
    </div>
  );
};

/* ─── product detail sheet ────────────────────────────────── */

interface ProductDetailProps {
  product: Product;
  marketName: string;
  onClose: () => void;
}

const ProductDetailSheet: React.FC<ProductDetailProps> = ({ product, marketName, onClose }) => {
  const [history, setHistory] = useState<PriceHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Swipe-to-dismiss
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartY = useRef(0);
  const dragCurrentY = useRef(0);

  const handleDismiss = () => {
    setDragY(window.innerHeight);
    setTimeout(onClose, 260);
  };

  const onDragStart = (e: React.TouchEvent) => {
    dragStartY.current = e.touches[0].clientY;
    dragCurrentY.current = 0;
    setIsDragging(true);
  };

  const onDragMove = (e: React.TouchEvent) => {
    const delta = e.touches[0].clientY - dragStartY.current;
    if (delta > 0) {
      dragCurrentY.current = delta;
      setDragY(delta);
    }
  };

  const onDragEnd = () => {
    setIsDragging(false);
    if (dragCurrentY.current > 120) {
      handleDismiss();
    } else {
      setDragY(0);
    }
  };

  useEffect(() => {
    let cancelled = false;
    setLoadingHistory(true);
    productService
      .getPriceHistory(product.ean, product.ncm, product.market_id)
      .then(res => {
        if (!cancelled) setHistory(res.history);
      })
      .catch(() => {
        if (!cancelled) setHistory([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false);
      });
    return () => { cancelled = true; };
  }, [product.ean, product.ncm, product.market_id]);

  const minPrice = history.length ? Math.min(...history.map(h => h.price)) : 0;
  const maxPrice = history.length ? Math.max(...history.map(h => h.price)) : 0;
  const priceChanged = history.length > 1 && history[history.length - 1].price !== history[0].price;
  const priceDiff = history.length > 1
    ? history[history.length - 1].price - history[0].price
    : 0;

  return (
    <div className="fixed inset-0 z-[200] flex items-end animate-in slide-in-from-bottom duration-300" style={{ touchAction: 'pan-y' }}>
      <div
        className="relative w-full flex flex-col overflow-hidden"
        style={{
          backgroundColor: 'var(--color-background)',
          height: '100dvh',
          transform: `translateY(${dragY}px)`,
          transition: isDragging ? 'none' : 'transform 260ms ease',
        }}
      >
        {/* Drag handle pill */}
        <div
          className="flex justify-center items-center shrink-0 cursor-grab active:cursor-grabbing"
          style={{
            paddingTop: '12px',
            paddingBottom: '12px',
            backgroundColor: 'var(--color-surface)',
            touchAction: 'none',
          }}
          onTouchStart={onDragStart}
          onTouchMove={onDragMove}
          onTouchEnd={onDragEnd}
        >
          <div className="w-10 h-1.5 rounded-full" style={{ backgroundColor: '#CBD5E1' }} />
        </div>

        {/* Sticky top bar */}
        <div
          className="flex items-center gap-3 px-4 py-3 shrink-0"
          style={{
            backgroundColor: 'var(--color-surface)',
            borderBottom: '1px solid var(--color-border)',
          }}
        >
          <button
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded-full cursor-pointer transition-opacity duration-150 active:opacity-70"
            style={{ backgroundColor: '#F1F5F9' }}
          >
            <ArrowLeft className="w-4 h-4" style={{ color: 'var(--color-text)' }} />
          </button>
          <p
            className="flex-1 text-sm font-semibold truncate"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
          >
            {product.product_name}
          </p>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-auto" style={{ overscrollBehavior: 'contain' }}>

          {/* Hero image */}
          <div
            className="w-full flex items-center justify-center py-8"
            style={{ backgroundColor: '#EFF6FF' }}
          >
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.product_name}
                className="w-40 h-40 object-contain rounded-2xl"
                onError={e => {
                  (e.target as HTMLImageElement).style.display = 'none';
                  (e.target as HTMLImageElement).nextElementSibling?.removeAttribute('style');
                }}
              />
            ) : null}
            <div
              className="w-40 h-40 rounded-2xl flex items-center justify-center"
              style={{
                backgroundColor: '#DBEAFE',
                display: product.image_url ? 'none' : 'flex',
              }}
            >
              <Package className="w-16 h-16" style={{ color: '#93C5FD' }} />
            </div>
          </div>

          <div className="p-4 space-y-4">

            {/* Name + price card */}
            <div
              className="rounded-2xl p-4"
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <h2
                className="text-lg font-bold leading-snug mb-3"
                style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
              >
                {product.product_name}
              </h2>

              <div className="flex items-end justify-between">
                <div>
                  <p className="text-xs mb-1" style={{ color: 'var(--color-text-muted)' }}>
                    Preço atual
                  </p>
                  <p
                    className="text-3xl font-bold"
                    style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-cta)' }}
                  >
                    R$ {(product.price || 0).toFixed(2)}
                  </p>
                </div>

                <div className="text-right space-y-1">
                  <span
                    className="inline-block text-xs px-2 py-0.5 rounded-lg"
                    style={{
                      backgroundColor: '#F1F5F9',
                      color: 'var(--color-text-muted)',
                      border: '1px solid var(--color-border)',
                    }}
                  >
                    {product.unidade_comercial}
                  </span>
                  {timeAgo(product.purchase_date) && (
                    <p className="text-xs" style={{ color: '#94A3B8' }}>
                      {timeAgo(product.purchase_date)}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Price history chart */}
            <div
              className="rounded-2xl p-4"
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
                  <h3
                    className="text-sm font-bold"
                    style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
                  >
                    Histórico de Preços
                  </h3>
                </div>

                {priceChanged && (
                  <span
                    className="text-xs font-semibold px-2 py-0.5 rounded-lg"
                    style={{
                      backgroundColor: priceDiff > 0 ? '#FEF2F2' : '#F0FDF4',
                      color: priceDiff > 0 ? '#EF4444' : '#22C55E',
                    }}
                  >
                    {priceDiff > 0 ? '+' : ''}R$ {priceDiff.toFixed(2)}
                  </span>
                )}
              </div>

              {loadingHistory ? (
                <div className="flex justify-center py-10">
                  <div
                    className="w-6 h-6 border-[3px] border-t-transparent rounded-full animate-spin"
                    style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }}
                  />
                </div>
              ) : history.length < 2 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <TrendingUp className="w-8 h-8 mb-2" style={{ color: '#CBD5E1' }} />
                  <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                    Dados insuficientes
                  </p>
                  <p className="text-xs mt-1" style={{ color: '#94A3B8' }}>
                    Histórico disponível após múltiplas compras
                  </p>
                </div>
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={history} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#F97316" stopOpacity={0.15} />
                          <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
                      <XAxis
                        dataKey="date"
                        tickFormatter={fmtDate}
                        tick={{ fontSize: 10, fill: '#94A3B8' }}
                        axisLine={false}
                        tickLine={false}
                        interval="preserveStartEnd"
                      />
                      <YAxis
                        tick={{ fontSize: 10, fill: '#94A3B8' }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={v => `${v.toFixed(0)}`}
                        domain={['auto', 'auto']}
                      />
                      <Tooltip content={<PriceTooltip />} />
                      <Line
                        type="monotone"
                        dataKey="price"
                        stroke="#F97316"
                        strokeWidth={2.5}
                        dot={false}
                        activeDot={{ r: 5, fill: '#F97316', strokeWidth: 0 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>

                  {/* Min / Max summary */}
                  <div
                    className="flex justify-between mt-3 pt-3"
                    style={{ borderTop: '1px solid var(--color-border)' }}
                  >
                    <div className="text-center">
                      <p className="text-xs" style={{ color: '#94A3B8' }}>Mínimo</p>
                      <p className="text-sm font-bold" style={{ color: '#22C55E' }}>
                        R$ {minPrice.toFixed(2)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs" style={{ color: '#94A3B8' }}>Registros</p>
                      <p className="text-sm font-bold" style={{ color: 'var(--color-text)' }}>
                        {history.length}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs" style={{ color: '#94A3B8' }}>Máximo</p>
                      <p className="text-sm font-bold" style={{ color: '#EF4444' }}>
                        R$ {maxPrice.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Details card */}
            <div
              className="rounded-2xl p-4 space-y-3"
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <h3
                className="text-sm font-bold"
                style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
              >
                Detalhes
              </h3>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Mercado</span>
                  <span className="text-xs font-semibold text-right max-w-[60%] text-right leading-tight" style={{ color: 'var(--color-text)' }}>
                    {marketName}
                  </span>
                </div>

                {product.ean && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs flex items-center gap-1" style={{ color: 'var(--color-text-muted)' }}>
                      <Barcode className="w-3 h-3" /> EAN
                    </span>
                    <span
                      className="text-xs font-mono px-2 py-0.5 rounded"
                      style={{
                        backgroundColor: '#F8FAFC',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text)',
                      }}
                    >
                      {product.ean}
                    </span>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Unidade</span>
                  <span className="text-xs font-semibold" style={{ color: 'var(--color-text)' }}>
                    {product.unidade_comercial}
                  </span>
                </div>

                {product.purchase_date && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Última atualização</span>
                    <span className="text-xs font-semibold" style={{ color: 'var(--color-text)' }}>
                      {new Date(product.purchase_date).toLocaleDateString('pt-BR')}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* bottom spacer for safe area */}
            <div className="h-6" />
          </div>
        </div>
      </div>
    </div>
  );
};

/* ─── main page ───────────────────────────────────────────── */

const MarketsPage: React.FC = () => {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);
  const [marketProducts, setMarketProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [productSearchTerm, setProductSearchTerm] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Swipe-to-dismiss state for the products sheet
  const [sheetDragY, setSheetDragY] = useState(0);
  const [isSheetDragging, setIsSheetDragging] = useState(false);
  const sheetDragStartY = useRef(0);
  const sheetDragCurrentY = useRef(0);

  const dismissSheet = useCallback(() => {
    setSheetDragY(window.innerHeight);
    setTimeout(() => {
      setSelectedMarket(null);
      setSheetDragY(0);
    }, 260);
  }, []);

  const onSheetDragStart = (e: React.TouchEvent) => {
    sheetDragStartY.current = e.touches[0].clientY;
    sheetDragCurrentY.current = 0;
    setIsSheetDragging(true);
  };

  const onSheetDragMove = (e: React.TouchEvent) => {
    const delta = e.touches[0].clientY - sheetDragStartY.current;
    if (delta > 0) {
      sheetDragCurrentY.current = delta;
      setSheetDragY(delta);
    }
  };

  const onSheetDragEnd = () => {
    setIsSheetDragging(false);
    if (sheetDragCurrentY.current > 120) {
      dismissSheet();
    } else {
      setSheetDragY(0);
    }
  };

  // Reset drag position when sheet opens
  useEffect(() => {
    if (selectedMarket) setSheetDragY(0);
  }, [selectedMarket]);

  useEffect(() => {
    fetchMarkets();
  }, []);

  // Lock body scroll whenever any sheet is open so the background page doesn't scroll
  useEffect(() => {
    const isSheetOpen = selectedMarket !== null || selectedProduct !== null;
    document.body.style.overflow = isSheetOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [selectedMarket, selectedProduct]);

  const fetchMarkets = async () => {
    try {
      const data = await marketService.getMarkets();
      setMarkets(data);
    } catch (error) {
      console.error('Failed to fetch markets', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarketClick = async (market: Market) => {
    setSelectedMarket(market);
    setLoadingProducts(true);
    setProductSearchTerm('');
    setSelectedProduct(null);
    try {
      const data = await marketService.getMarketProducts(market.market_id);
      setMarketProducts(data.products);
    } catch (error) {
      console.error('Failed to fetch products', error);
    } finally {
      setLoadingProducts(false);
    }
  };

  const filteredMarkets = markets.filter(
    m =>
      m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.address.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const filteredProducts = useMemo(() => {
    if (!productSearchTerm.trim()) return marketProducts;
    const query = productSearchTerm.toLowerCase();
    return marketProducts.filter(p => p.product_name.toLowerCase().includes(query));
  }, [marketProducts, productSearchTerm]);

  return (
    <div
      className="p-4 space-y-5"
      style={{ fontFamily: 'var(--font-body)', color: 'var(--color-text)' }}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
        <div>
          <h1
            className="text-2xl font-bold"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
          >
            Mercados
          </h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            {markets.length} mercados disponíveis
          </p>
        </div>

        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
            style={{ color: 'var(--color-text-muted)' }}
          />
          <input
            type="text"
            placeholder="Buscar mercados..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="pl-9 pr-4 py-2.5 rounded-xl text-sm w-full sm:w-56"
            style={{
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-body)',
              outline: 'none',
              transition: 'border-color 200ms ease',
            }}
            onFocus={e => (e.target.style.borderColor = 'var(--color-primary)')}
            onBlur={e => (e.target.style.borderColor = 'var(--color-border)')}
          />
        </div>
      </div>

      {/* Market Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div
            className="w-8 h-8 border-[3px] border-t-transparent rounded-full animate-spin"
            style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredMarkets.map(market => (
            <button
              key={market.market_id}
              onClick={() => handleMarketClick(market)}
              className="text-left rounded-xl p-4 cursor-pointer transition-opacity duration-150 active:opacity-70"
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className="flex items-center justify-center w-10 h-10 rounded-xl"
                  style={{ backgroundColor: '#EFF6FF' }}
                >
                  <Store className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
                </div>
              </div>

              <h3
                className="font-semibold text-sm leading-tight mb-1.5 truncate"
                style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
              >
                {market.name}
              </h3>

              <p
                className="text-xs flex items-start gap-1 line-clamp-2"
                style={{ color: 'var(--color-text-muted)' }}
              >
                <MapPin className="w-3 h-3 mt-0.5 shrink-0" />
                {market.address}
              </p>
            </button>
          ))}

          {filteredMarkets.length === 0 && (
            <div className="col-span-full flex flex-col items-center justify-center py-20 text-center">
              <div
                className="w-14 h-14 flex items-center justify-center rounded-2xl mb-4"
                style={{ backgroundColor: '#F8FAFC' }}
              >
                <Store className="w-7 h-7" style={{ color: '#CBD5E1' }} />
              </div>
              <p className="font-medium" style={{ color: 'var(--color-text-muted)' }}>
                Nenhum mercado encontrado
              </p>
              <p className="text-xs mt-1" style={{ color: '#94A3B8' }}>
                Tente outro termo de busca.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Market Products Full-Screen Sheet */}
      {selectedMarket && (
        <div className="fixed inset-0 z-[100] flex items-end" style={{ touchAction: 'pan-y' }}>
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setSelectedMarket(null)}
          />

          {/* Sheet */}
          <div
            className="relative w-full flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-300"
            style={{
              backgroundColor: 'var(--color-surface)',
              borderRadius: '20px 20px 0 0',
              height: '100dvh',
              boxShadow: 'var(--shadow-xl)',
              transform: `translateY(${sheetDragY}px)`,
              transition: isSheetDragging ? 'none' : 'transform 260ms ease',
            }}
          >
            {/* Drag handle pill — full-width touch target */}
            <div
              className="flex justify-center items-center shrink-0 cursor-grab active:cursor-grabbing"
              style={{ paddingTop: '12px', paddingBottom: '12px', touchAction: 'none' }}
              onTouchStart={onSheetDragStart}
              onTouchMove={onSheetDragMove}
              onTouchEnd={onSheetDragEnd}
            >
              <div
                className="w-10 h-1.5 rounded-full"
                style={{ backgroundColor: '#CBD5E1' }}
              />
            </div>

            {/* Modal Header */}
            <div
              className="px-5 py-3 sticky top-0 z-10 space-y-3 shrink-0"
              style={{
                backgroundColor: 'var(--color-surface)',
                borderBottom: '1px solid var(--color-border)',
              }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className="flex items-center justify-center w-10 h-10 rounded-xl shrink-0"
                    style={{ backgroundColor: '#EFF6FF' }}
                  >
                    <Store className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
                  </div>
                  <div className="min-w-0">
                    <h3
                      className="font-bold text-base leading-tight"
                      style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
                    >
                      {selectedMarket.name}
                    </h3>
                    <p
                      className="text-xs mt-0.5 line-clamp-1"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      {selectedMarket.address}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedMarket(null)}
                  className="shrink-0 flex items-center justify-center w-8 h-8 rounded-full cursor-pointer transition-opacity duration-150 active:opacity-70"
                  style={{ backgroundColor: '#F1F5F9' }}
                >
                  <X className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
                </button>
              </div>

              <div className="relative">
                <Search
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
                  style={{ color: 'var(--color-text-muted)' }}
                />
                <input
                  type="text"
                  placeholder="Buscar produtos..."
                  value={productSearchTerm}
                  onChange={e => setProductSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl text-sm"
                  style={{
                    border: '1px solid var(--color-border)',
                    backgroundColor: '#F8FAFC',
                    color: 'var(--color-text)',
                    fontFamily: 'var(--font-body)',
                    outline: 'none',
                  }}
                  onFocus={e => (e.target.style.borderColor = 'var(--color-primary)')}
                  onBlur={e => (e.target.style.borderColor = 'var(--color-border)')}
                />
              </div>
            </div>

            {/* Product List */}
            <div className="flex-1 overflow-auto p-4" style={{ overscrollBehavior: 'contain' }}>
              {loadingProducts ? (
                <div className="flex justify-center py-20">
                  <div
                    className="w-8 h-8 border-[3px] border-t-transparent rounded-full animate-spin"
                    style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }}
                  />
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredProducts.map(product => (
                    <button
                      key={product.id}
                      onClick={() => setSelectedProduct(product)}
                      className="w-full flex items-center gap-3 p-3 rounded-xl text-left cursor-pointer transition-opacity duration-150 active:opacity-70"
                      style={{
                        backgroundColor: '#F8FAFC',
                        border: '1px solid var(--color-border)',
                      }}
                    >
                      {/* Product Image */}
                      {product.image_url ? (
                        <div
                          className="w-11 h-11 rounded-lg shrink-0 overflow-hidden flex items-center justify-center"
                          style={{
                            backgroundColor: 'var(--color-surface)',
                            border: '1px solid var(--color-border)',
                          }}
                        >
                          <img
                            src={product.image_url}
                            alt={product.product_name}
                            className="w-full h-full object-contain"
                            onError={e => {
                              (e.target as HTMLImageElement).src =
                                'https://placehold.co/80x80?text=N/A';
                            }}
                          />
                        </div>
                      ) : (
                        <div
                          className="w-11 h-11 rounded-lg shrink-0 flex items-center justify-center"
                          style={{ backgroundColor: '#F1F5F9' }}
                        >
                          <Package className="w-5 h-5" style={{ color: '#CBD5E1' }} />
                        </div>
                      )}

                      {/* Product Info */}
                      <div className="flex-1 min-w-0">
                        <p
                          className="text-sm font-semibold line-clamp-2 leading-tight"
                          style={{ color: 'var(--color-text)', fontFamily: 'var(--font-body)' }}
                        >
                          {product.product_name}
                        </p>
                        <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                          <span
                            className="text-xs px-1.5 py-0.5 rounded"
                            style={{
                              backgroundColor: 'var(--color-surface)',
                              color: 'var(--color-text-muted)',
                              border: '1px solid var(--color-border)',
                            }}
                          >
                            {product.unidade_comercial}
                          </span>
                          {timeAgo(product.purchase_date) && (
                            <span className="text-xs" style={{ color: '#94A3B8' }}>
                              · {timeAgo(product.purchase_date)}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Price */}
                      <div className="shrink-0 text-right">
                        <p
                          className="font-bold text-sm"
                          style={{ color: 'var(--color-cta)', fontFamily: 'var(--font-heading)' }}
                        >
                          R$ {(product.price || 0).toFixed(2)}
                        </p>
                      </div>
                    </button>
                  ))}

                  {filteredProducts.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                      <div
                        className="w-12 h-12 flex items-center justify-center rounded-2xl mb-3"
                        style={{ backgroundColor: '#F8FAFC' }}
                      >
                        <Package className="w-6 h-6" style={{ color: '#CBD5E1' }} />
                      </div>
                      <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                        Nenhum produto encontrado
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Product Detail Sheet — renders on top of market products sheet */}
      {selectedProduct && selectedMarket && (
        <ProductDetailSheet
          product={selectedProduct}
          marketName={selectedMarket.name}
          onClose={() => setSelectedProduct(null)}
        />
      )}
    </div>
  );
};

export default MarketsPage;
