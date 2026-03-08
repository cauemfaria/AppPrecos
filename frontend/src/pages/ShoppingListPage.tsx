import React, { useState, useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { productService, marketService } from '../services/api';
import type { ProductSearchItem, Market, CompareResponse, BestMarketsResponse } from '../types';
import {
  Search, Plus, Trash2, Store,
  ArrowRightLeft, Check, X,
  TrendingDown, AlertCircle, ShoppingBasket,
  Package, MapPin, Award, Loader2,
} from 'lucide-react';

const MAX_MARKETS_FOR_COMPARISON = 5;

/* ─── ModalWrapper ─────────────────────────────────────────── */

const ModalWrapper: React.FC<{
  onClose: () => void;
  children: React.ReactNode;
  zIndex?: number;
}> = ({ onClose, children, zIndex = 100 }) => {
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

  return (
    <div
      className="fixed inset-0 flex items-end justify-center"
      style={{ zIndex, touchAction: 'pan-y' }}
    >
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-pointer"
        onClick={onClose}
      />
      <div
        className="relative w-full flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-300"
        style={{
          backgroundColor: 'var(--color-surface)',
          boxShadow: 'var(--shadow-xl)',
          borderRadius: '20px 20px 0 0',
          height: '100dvh',
          transform: `translateY(${dragY}px)`,
          transition: isDragging ? 'none' : 'transform 260ms ease',
        }}
      >
        {/* Drag handle pill */}
        <div
          className="flex justify-center items-center shrink-0 cursor-grab active:cursor-grabbing"
          style={{ paddingTop: '12px', paddingBottom: '12px', touchAction: 'none' }}
          onTouchStart={onDragStart}
          onTouchMove={onDragMove}
          onTouchEnd={onDragEnd}
        >
          <div className="w-10 h-1.5 rounded-full" style={{ backgroundColor: '#CBD5E1' }} />
        </div>
        {children}
      </div>
    </div>
  );
};

/* ─── ModalHeader ──────────────────────────────────────────── */

const ModalHeader: React.FC<{
  title: string;
  subtitle?: string;
  onClose: () => void;
  children?: React.ReactNode;
}> = ({ title, subtitle, onClose, children }) => (
  <div
    className="px-5 py-4 sticky top-0 z-10 space-y-3 shrink-0"
    style={{ backgroundColor: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)' }}
  >
    <div className="flex items-start justify-between gap-3">
      <div>
        <h3
          className="font-bold text-base"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
        >
          {title}
        </h3>
        {subtitle && (
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            {subtitle}
          </p>
        )}
      </div>
      <button
        onClick={onClose}
        className="flex items-center justify-center w-8 h-8 rounded-full cursor-pointer transition-opacity duration-150 active:opacity-70 shrink-0"
        style={{ backgroundColor: '#F1F5F9' }}
      >
        <X className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
      </button>
    </div>
    {children}
  </div>
);

/* ─── Main page ────────────────────────────────────────────── */

const ShoppingListPage: React.FC = () => {
  const {
    shoppingList, addToShoppingList, removeFromShoppingList, clearShoppingList,
    selectedMarketIds, toggleMarketSelection,
  } = useStore();

  const [markets, setMarkets] = useState<Market[]>([]);
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<ProductSearchItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [isMarketModalOpen, setIsMarketModalOpen] = useState(false);
  const [isLoadingMarkets, setIsLoadingMarkets] = useState(false);
  const [marketsError, setMarketsError] = useState<string | null>(null);
  const [marketLimitError, setMarketLimitError] = useState<string | null>(null);

  const [isComparisonOpen, setIsComparisonOpen] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<CompareResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [isBestPlacesOpen, setIsBestPlacesOpen] = useState(false);
  const [bestPlacesResult, setBestPlacesResult] = useState<BestMarketsResponse | null>(null);
  const [isFetchingBestPlaces, setIsFetchingBestPlaces] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductSearchItem | null>(null);

  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { fetchMarkets(); }, []);

  // Lock body scroll when any sheet is open
  useEffect(() => {
    const anyOpen = isSearchModalOpen || isMarketModalOpen || isComparisonOpen || isBestPlacesOpen;
    document.body.style.overflow = anyOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [isSearchModalOpen, isMarketModalOpen, isComparisonOpen, isBestPlacesOpen]);

  // Auto-focus search input without triggering iOS zoom (font-size must be >=16px)
  useEffect(() => {
    if (isSearchModalOpen) {
      const t = setTimeout(() => searchInputRef.current?.focus(), 150);
      return () => clearTimeout(t);
    }
  }, [isSearchModalOpen]);

  const fetchMarkets = async () => {
    setIsLoadingMarkets(true);
    setMarketsError(null);
    try {
      const data = await marketService.getMarkets();
      setMarkets(data);
    } catch (error: any) {
      const message = (error as any).isBackendDown
        ? (error as any).backendErrorMessage
        : error.response?.data?.error || error.message || 'Falha ao buscar mercados';
      setMarketsError(message);
    } finally {
      setIsLoadingMarkets(false);
    }
  };

  const handleSearch = (query: string) => {
    setSearchTerm(query);
    setSearchError(null);
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    if (query.length < 2) { setSearchResults([]); return; }
    searchDebounceRef.current = setTimeout(() => performSearch(query), 500);
  };

  const performSearch = async (query: string) => {
    setIsSearching(true);
    setSearchError(null);
    try {
      const data = await productService.searchProducts(query);
      setSearchResults(data.results);
    } catch (error: any) {
      const message = (error as any).isBackendDown
        ? (error as any).backendErrorMessage
        : error.response?.data?.error || error.message || 'Busca falhou';
      setSearchError(message);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleToggleMarket = (marketId: string) => {
    if (!selectedMarketIds.includes(marketId) && selectedMarketIds.length >= MAX_MARKETS_FOR_COMPARISON) {
      setMarketLimitError(`Máximo de ${MAX_MARKETS_FOR_COMPARISON} mercados permitidos`);
      setTimeout(() => setMarketLimitError(null), 3000);
      return;
    }
    toggleMarketSelection(marketId);
  };

  const handleCompare = async () => {
    if (shoppingList.length === 0) { setError('Adicione produtos à lista primeiro'); setTimeout(() => setError(null), 3000); return; }
    if (selectedMarketIds.length === 0) { setError('Selecione pelo menos um mercado'); setTimeout(() => setError(null), 3000); return; }
    setIsComparing(true);
    try {
      const result = await productService.compareProducts({
        products: shoppingList.map(p => ({ ean: p.ean, ncm: p.ncm, product_name: p.product_name })),
        market_ids: selectedMarketIds,
      });
      setComparisonResult(result);
      setIsComparisonOpen(true);
    } catch (error: any) {
      const message = (error as any).isBackendDown
        ? (error as any).backendErrorMessage
        : error.response?.data?.error || error.message || 'Comparação falhou';
      setError(message);
      setTimeout(() => setError(null), 3000);
    } finally {
      setIsComparing(false);
    }
  };

  const handleProductClick = async (product: ProductSearchItem) => {
    setSelectedProduct(product);
    setIsBestPlacesOpen(true);
    setIsFetchingBestPlaces(true);
    try {
      const result = await productService.getBestMarketsForProduct(
        { ean: product.ean, ncm: product.ncm, product_name: product.product_name }, 3,
      );
      setBestPlacesResult(result);
    } catch (error: any) {
      const message = (error as any).isBackendDown
        ? (error as any).backendErrorMessage
        : error.response?.data?.error || error.message || 'Falha ao buscar melhores mercados';
      setError(message);
      setTimeout(() => setError(null), 3000);
    } finally {
      setIsFetchingBestPlaces(false);
    }
  };

  return (
    <div
      className="p-4 pb-44"
      style={{ fontFamily: 'var(--font-body)', color: 'var(--color-text)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between pt-2 mb-5">
        <div>
          <h1
            className="text-2xl font-bold"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
          >
            Lista de Compras
          </h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            {shoppingList.length} {shoppingList.length === 1 ? 'produto' : 'produtos'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {shoppingList.length > 0 && (
            <button
              onClick={clearShoppingList}
              className="flex items-center justify-center w-9 h-9 rounded-xl cursor-pointer transition-opacity duration-150 active:opacity-70"
              style={{ backgroundColor: '#FEF2F2' }}
              title="Limpar lista"
            >
              <Trash2 className="w-4 h-4" style={{ color: '#EF4444' }} />
            </button>
          )}
          <button
            onClick={() => setIsSearchModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-semibold text-sm cursor-pointer transition-opacity duration-150 active:opacity-80"
            style={{
              backgroundColor: 'var(--color-cta)',
              color: 'white',
              fontFamily: 'var(--font-body)',
              boxShadow: '0 2px 8px rgba(249,115,22,0.25)',
            }}
          >
            <Plus className="w-4 h-4" />
            Adicionar
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div
          className="mb-4 flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium"
          style={{
            backgroundColor: '#FEF2F2',
            border: '1px solid #FECACA',
            color: '#DC2626',
          }}
        >
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Product List */}
      <div className="space-y-2">
        {shoppingList.length === 0 ? (
          <div
            className="flex flex-col items-center justify-center py-16 rounded-2xl text-center"
            style={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div
              className="w-14 h-14 flex items-center justify-center rounded-2xl mb-3"
              style={{ backgroundColor: '#F8FAFC' }}
            >
              <ShoppingBasket className="w-7 h-7" style={{ color: '#CBD5E1' }} />
            </div>
            <p className="font-semibold" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-heading)' }}>
              Sua lista está vazia
            </p>
            <p className="text-xs mt-1 max-w-[180px]" style={{ color: '#94A3B8' }}>
              Adicione produtos para comparar preços.
            </p>
          </div>
        ) : (
          shoppingList.map((product, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 p-3 rounded-xl"
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <button
                onClick={() => handleProductClick(product)}
                className="flex items-center gap-3 flex-1 min-w-0 text-left cursor-pointer transition-opacity duration-150 active:opacity-70"
              >
                {product.image_url ? (
                  <div
                    className="w-11 h-11 rounded-lg shrink-0 overflow-hidden flex items-center justify-center"
                    style={{ backgroundColor: '#F8FAFC', border: '1px solid var(--color-border)' }}
                  >
                    <img src={product.image_url} alt={product.product_name} className="w-full h-full object-contain" />
                  </div>
                ) : (
                  <div
                    className="w-11 h-11 rounded-lg shrink-0 flex items-center justify-center"
                    style={{ backgroundColor: '#F1F5F9' }}
                  >
                    <Package className="w-5 h-5" style={{ color: '#CBD5E1' }} />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p
                    className="text-sm font-semibold line-clamp-2 leading-tight"
                    style={{ color: 'var(--color-text)', fontFamily: 'var(--font-body)' }}
                  >
                    {product.product_name}
                  </p>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span
                      className="text-xs px-1.5 py-0.5 rounded font-medium"
                      style={{
                        backgroundColor: '#EFF6FF',
                        color: 'var(--color-primary)',
                        border: '1px solid #BFDBFE',
                      }}
                    >
                      {product.unidade_comercial}
                    </span>
                    <span className="text-xs" style={{ color: '#94A3B8' }}>
                      R$ {product.min_price?.toFixed(2) || '0.00'} – {product.max_price?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                  <p className="text-xs mt-0.5" style={{ color: 'var(--color-primary)' }}>
                    Ver melhores lugares →
                  </p>
                </div>
              </button>
              <button
                onClick={() => removeFromShoppingList(product)}
                className="shrink-0 flex items-center justify-center w-8 h-8 rounded-lg cursor-pointer transition-opacity duration-150 active:opacity-70"
                style={{ backgroundColor: '#FEF2F2' }}
              >
                <Trash2 className="w-4 h-4" style={{ color: '#EF4444' }} />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Market Selector Bar — docked above bottom nav */}
      <div
        className="fixed left-0 right-0 z-40 px-4 pb-2"
        style={{ bottom: 'calc(64px + env(safe-area-inset-bottom, 0px))' }}
      >
        <div
          className="flex items-center gap-3 p-3 rounded-2xl"
          style={{
            backgroundColor: 'var(--color-surface)',
            boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
            border: '1px solid var(--color-border)',
          }}
        >
          <button
            onClick={() => setIsMarketModalOpen(true)}
            className="flex items-center gap-2.5 flex-1 min-w-0 cursor-pointer text-left transition-opacity duration-150 active:opacity-70"
          >
            <div
              className="flex items-center justify-center w-9 h-9 rounded-xl shrink-0"
              style={{ backgroundColor: '#EFF6FF' }}
            >
              <Store className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase tracking-wider" style={{ color: '#94A3B8' }}>
                Mercados
              </p>
              <p
                className="text-sm font-semibold truncate"
                style={{ color: 'var(--color-text)', fontFamily: 'var(--font-body)' }}
              >
                {selectedMarketIds.length === 0
                  ? 'Nenhum selecionado'
                  : `${selectedMarketIds.length} de ${MAX_MARKETS_FOR_COMPARISON}`}
              </p>
            </div>
          </button>

          <button
            onClick={handleCompare}
            disabled={shoppingList.length === 0 || selectedMarketIds.length === 0 || isComparing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm cursor-pointer transition-opacity duration-150 active:opacity-80 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              backgroundColor: 'var(--color-primary)',
              color: 'white',
              fontFamily: 'var(--font-body)',
            }}
          >
            {isComparing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ArrowRightLeft className="w-4 h-4" />
            )}
            Comparar
          </button>
        </div>
      </div>

      {/* === MODAL 1: Add Product Search === */}
      {isSearchModalOpen && (
        <ModalWrapper onClose={() => { setIsSearchModalOpen(false); setSearchTerm(''); setSearchResults([]); }} zIndex={100}>
          <ModalHeader title="Adicionar Produto" onClose={() => { setIsSearchModalOpen(false); setSearchTerm(''); setSearchResults([]); }}>
            {searchError && (
              <div
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs"
                style={{ backgroundColor: '#FEF2F2', color: '#DC2626', border: '1px solid #FECACA' }}
              >
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                {searchError}
              </div>
            )}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Buscar produtos por nome..."
                value={searchTerm}
                onChange={e => handleSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 rounded-xl"
                style={{
                  fontSize: '16px',
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
          </ModalHeader>

          <div className="flex-1 overflow-auto p-4 space-y-2" style={{ overscrollBehavior: 'contain' }}>
            {isSearching ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin" style={{ color: 'var(--color-primary)' }} />
              </div>
            ) : searchResults.length > 0 ? (
              searchResults.map((product, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    addToShoppingList(product);
                    setSearchResults(prev => prev.filter((_, i) => i !== idx));
                  }}
                  className="w-full text-left flex items-center justify-between gap-3 p-3 rounded-xl cursor-pointer transition-opacity duration-150 active:opacity-70"
                  style={{
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-surface)',
                  }}
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {product.image_url ? (
                      <div className="w-10 h-10 rounded-lg shrink-0 overflow-hidden" style={{ backgroundColor: '#F8FAFC', border: '1px solid var(--color-border)' }}>
                        <img src={product.image_url} alt={product.product_name} className="w-full h-full object-contain" />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-lg shrink-0 flex items-center justify-center" style={{ backgroundColor: '#F1F5F9' }}>
                        <Package className="w-5 h-5" style={{ color: '#CBD5E1' }} />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold line-clamp-2 leading-tight" style={{ color: 'var(--color-text)' }}>
                        {product.product_name}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                        {product.markets_count} mercados
                      </p>
                    </div>
                  </div>
                  <Plus className="w-4 h-4 shrink-0" style={{ color: 'var(--color-cta)' }} />
                </button>
              ))
            ) : (
              <div className="text-center py-12">
                <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                  {searchTerm.length < 2
                    ? 'Digite pelo menos 2 caracteres para buscar...'
                    : `Nenhum produto encontrado para "${searchTerm}"`}
                </p>
              </div>
            )}
          </div>
        </ModalWrapper>
      )}

      {/* === MODAL 2: Market Selection === */}
      {isMarketModalOpen && (
        <ModalWrapper onClose={() => setIsMarketModalOpen(false)} zIndex={100}>
          <ModalHeader
            title="Selecionar Mercados"
            subtitle={`Escolha até ${MAX_MARKETS_FOR_COMPARISON} mercados para comparar`}
            onClose={() => setIsMarketModalOpen(false)}
          />

          {isLoadingMarkets ? (
            <div className="flex-1 flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin" style={{ color: 'var(--color-primary)' }} />
            </div>
          ) : marketsError ? (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
              <AlertCircle className="w-10 h-10 mb-3" style={{ color: '#EF4444' }} />
              <p className="text-sm font-semibold mb-1" style={{ color: 'var(--color-text)' }}>
                Falha ao carregar mercados
              </p>
              <p className="text-xs mb-4" style={{ color: 'var(--color-text-muted)' }}>{marketsError}</p>
              <button
                onClick={fetchMarkets}
                className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer active:opacity-80"
                style={{ backgroundColor: 'var(--color-primary)', color: 'white' }}
              >
                Tentar Novamente
              </button>
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-auto p-4 space-y-2" style={{ overscrollBehavior: 'contain' }}>
                {/* Market limit error — shown inside the modal */}
                {marketLimitError && (
                  <div
                    className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium mb-1"
                    style={{
                      backgroundColor: '#FEF2F2',
                      border: '1px solid #FECACA',
                      color: '#DC2626',
                    }}
                  >
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    {marketLimitError}
                  </div>
                )}

                {markets.map(market => {
                  const isSelected = selectedMarketIds.includes(market.market_id);
                  return (
                    <button
                      key={market.market_id}
                      onClick={() => handleToggleMarket(market.market_id)}
                      className="w-full text-left flex items-center justify-between gap-3 p-3 rounded-xl cursor-pointer transition-opacity duration-150 active:opacity-70"
                      style={{
                        backgroundColor: isSelected ? '#EFF6FF' : 'var(--color-surface)',
                        border: `1px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-border)'}`,
                      }}
                    >
                      <div className="flex-1 min-w-0">
                        <p
                          className="text-sm font-semibold truncate"
                          style={{ color: isSelected ? 'var(--color-primary)' : 'var(--color-text)' }}
                        >
                          {market.name}
                        </p>
                        <p className="text-xs truncate" style={{ color: 'var(--color-text-muted)' }}>
                          {market.address}
                        </p>
                      </div>
                      <div
                        className="flex items-center justify-center w-6 h-6 rounded-lg shrink-0 transition-colors duration-150"
                        style={{
                          backgroundColor: isSelected ? 'var(--color-primary)' : 'var(--color-surface)',
                          border: `2px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-border)'}`,
                        }}
                      >
                        {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                      </div>
                    </button>
                  );
                })}

                {markets.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Nenhum mercado disponível</p>
                  </div>
                )}
              </div>
              <div
                className="p-4 shrink-0"
                style={{ borderTop: '1px solid var(--color-border)', backgroundColor: '#F8FAFC' }}
              >
                <button
                  onClick={() => setIsMarketModalOpen(false)}
                  className="w-full py-3 rounded-xl font-bold text-sm cursor-pointer transition-opacity duration-150 active:opacity-80"
                  style={{ backgroundColor: 'var(--color-text)', color: 'white', fontFamily: 'var(--font-body)' }}
                >
                  Pronto ({selectedMarketIds.length})
                </button>
              </div>
            </>
          )}
        </ModalWrapper>
      )}

      {/* === MODAL 3: Comparison Results === */}
      {isComparisonOpen && comparisonResult && (() => {
        // Calculate best market for the full cart
        const marketEntries = Object.entries(comparisonResult.markets);
        const cartSummary = marketEntries.map(([mId, mName]) => {
          const prices = comparisonResult.comparison.map(row => row.prices[mId]).filter((p): p is number => p !== null);
          return { mId, mName, total: prices.reduce((s, p) => s + p, 0), count: prices.length };
        }).filter(m => m.count > 0).sort((a, b) => {
          if (b.count !== a.count) return b.count - a.count;
          return a.total - b.total;
        });
        const bestCart = cartSummary[0];
        const totalProducts = comparisonResult.comparison.length;

        return (
          <ModalWrapper onClose={() => setIsComparisonOpen(false)} zIndex={110}>
            <ModalHeader
              title="Comparação de Preços"
              subtitle={`${totalProducts} ${totalProducts === 1 ? 'produto' : 'produtos'} · ${marketEntries.length} mercados`}
              onClose={() => setIsComparisonOpen(false)}
            />
            <div className="flex-1 overflow-auto p-4 space-y-3" style={{ overscrollBehavior: 'contain' }}>

              {/* Best-cart summary card */}
              {bestCart && (
                <div
                  className="flex items-center gap-3 p-4 rounded-2xl"
                  style={{
                    background: 'linear-gradient(135deg, #F97316 0%, #EA580C 100%)',
                    boxShadow: '0 4px 12px rgba(249,115,22,0.25)',
                  }}
                >
                  <div
                    className="flex items-center justify-center w-10 h-10 rounded-xl shrink-0"
                    style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}
                  >
                    <TrendingDown className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold uppercase tracking-wide text-white/80">
                      Melhor opção para a lista
                    </p>
                    <p className="text-sm font-bold text-white truncate" style={{ fontFamily: 'var(--font-heading)' }}>
                      {bestCart.mName}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-lg font-bold text-white" style={{ fontFamily: 'var(--font-heading)' }}>
                      R$ {bestCart.total.toFixed(2)}
                    </p>
                    <p className="text-xs text-white/80">
                      {bestCart.count}/{totalProducts} itens
                    </p>
                  </div>
                </div>
              )}

              {/* Product comparison cards */}
              {comparisonResult.comparison.map((row, idx) => (
                <div
                  key={idx}
                  className="overflow-hidden rounded-2xl"
                  style={{
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-surface)',
                    boxShadow: 'var(--shadow-sm)',
                  }}
                >
                  {/* Product header — blue left-accent strip */}
                  <div
                    className="flex items-center gap-3 p-3 pl-4"
                    style={{
                      backgroundColor: '#EFF6FF',
                      borderBottom: '1px solid #BFDBFE',
                      borderLeft: '4px solid var(--color-primary)',
                    }}
                  >
                    {row.image_url ? (
                      <div
                        className="w-10 h-10 rounded-lg overflow-hidden shrink-0"
                        style={{ backgroundColor: 'white', border: '1px solid #DBEAFE' }}
                      >
                        <img src={row.image_url} alt={row.product_name} className="w-full h-full object-contain" />
                      </div>
                    ) : (
                      <div
                        className="w-10 h-10 rounded-lg shrink-0 flex items-center justify-center"
                        style={{ backgroundColor: '#DBEAFE' }}
                      >
                        <Package className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
                      </div>
                    )}
                    <p
                      className="text-sm font-bold line-clamp-2 leading-tight flex-1 min-w-0"
                      style={{ color: 'var(--color-primary)', fontFamily: 'var(--font-heading)' }}
                    >
                      {row.product_name}
                    </p>
                  </div>

                  {/* Market price rows */}
                  {Object.entries(comparisonResult.markets).map(([mId, mName], mIdx) => {
                    const price = row.prices[mId];
                    const isMin = price !== null && price === row.min_price && !row.all_equal;
                    const isMax = price !== null && price === row.max_price && !row.all_equal;
                    return (
                      <div
                        key={mId}
                        className="flex items-center justify-between px-4 py-2.5"
                        style={{
                          borderTop: mIdx > 0 ? '1px solid var(--color-border)' : undefined,
                          backgroundColor: isMin ? '#F0FDF4' : 'transparent',
                        }}
                      >
                        <p
                          className="text-sm truncate flex-1 mr-3"
                          style={{ color: isMin ? '#166534' : 'var(--color-text-muted)', fontWeight: isMin ? 600 : 400 }}
                        >
                          {mName}
                        </p>
                        {price == null ? (
                          <span className="text-sm font-medium" style={{ color: '#CBD5E1' }}>—</span>
                        ) : (
                          <div className="flex items-center gap-2 shrink-0">
                            {isMin && (
                              <span
                                className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full"
                                style={{ backgroundColor: '#DCFCE7', color: '#166534' }}
                              >
                                Melhor
                              </span>
                            )}
                            <span
                              className="text-sm font-bold"
                              style={{
                                color: isMin ? '#16A34A' : isMax ? '#EF4444' : 'var(--color-text)',
                              }}
                            >
                              R$ {price.toFixed(2)}
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}

              {/* Footer note */}
              <p
                className="text-xs text-center pb-2"
                style={{ color: '#94A3B8' }}
              >
                "—" indica produto não encontrado neste mercado
              </p>
            </div>
          </ModalWrapper>
        );
      })()}

      {/* === MODAL 4: Best Places === */}
      {isBestPlacesOpen && selectedProduct && (
        <ModalWrapper onClose={() => setIsBestPlacesOpen(false)} zIndex={120}>
          <ModalHeader
            title="Melhores Lugares"
            subtitle="Top 3 mercados com menor preço"
            onClose={() => setIsBestPlacesOpen(false)}
          >
            <div className="flex items-center gap-3">
              {selectedProduct.image_url ? (
                <div className="w-10 h-10 rounded-lg shrink-0 overflow-hidden" style={{ border: '1px solid var(--color-border)' }}>
                  <img src={selectedProduct.image_url} alt={selectedProduct.product_name} className="w-full h-full object-contain" />
                </div>
              ) : (
                <div className="w-10 h-10 rounded-lg shrink-0 flex items-center justify-center" style={{ backgroundColor: '#F1F5F9' }}>
                  <Package className="w-5 h-5" style={{ color: '#CBD5E1' }} />
                </div>
              )}
              <p className="text-sm font-semibold line-clamp-2 leading-tight" style={{ color: 'var(--color-text)' }}>
                {selectedProduct.product_name}
              </p>
            </div>
          </ModalHeader>

          <div className="flex-1 overflow-auto p-4 space-y-3" style={{ overscrollBehavior: 'contain' }}>
            {isFetchingBestPlaces ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin" style={{ color: 'var(--color-primary)' }} />
              </div>
            ) : bestPlacesResult && bestPlacesResult.best_markets.length > 0 ? (
              (() => {
                const priceGroups = bestPlacesResult.best_markets.reduce((acc, market) => {
                  const key = market.price.toFixed(2);
                  if (!acc[key]) acc[key] = [];
                  acc[key].push(market);
                  return acc;
                }, {} as Record<string, typeof bestPlacesResult.best_markets>);

                const uniquePrices = Object.keys(priceGroups).sort((a, b) => parseFloat(a) - parseFloat(b));

                const rankColors = [
                  { bg: '#F0FDF4', border: '#BBF7D0', iconBg: '#16A34A', text: '#166534', priceBg: '#DCFCE7', priceText: '#15803D' },
                  { bg: '#EFF6FF', border: '#BFDBFE', iconBg: '#2563EB', text: '#1E40AF', priceBg: '#DBEAFE', priceText: '#1D4ED8' },
                  { bg: '#FFF7ED', border: '#FED7AA', iconBg: '#F97316', text: '#9A3412', priceBg: '#FFEDD5', priceText: '#C2410C' },
                ];

                return uniquePrices.flatMap((priceKey, priceRank) =>
                  priceGroups[priceKey].map((market) => {
                    const colors = rankColors[Math.min(priceRank, 2)];
                    return (
                      <div
                        key={market.market_id}
                        className="rounded-xl overflow-hidden"
                        style={{ backgroundColor: colors.bg, border: `1px solid ${colors.border}` }}
                      >
                        <div className="flex items-center gap-3 p-4">
                          <div
                            className="flex items-center justify-center w-10 h-10 rounded-xl shrink-0"
                            style={{ backgroundColor: colors.iconBg }}
                          >
                            {priceRank === 0
                              ? <Award className="w-5 h-5 text-white" />
                              : <span className="font-bold text-base text-white">{priceRank + 1}</span>}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p
                              className="font-bold text-sm truncate"
                              style={{ color: colors.text, fontFamily: 'var(--font-heading)' }}
                            >
                              {market.market_name}
                            </p>
                            {priceRank === 0 && (
                              <span
                                className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full inline-block mt-0.5"
                                style={{ backgroundColor: colors.priceBg, color: colors.text }}
                              >
                                Melhor Preço
                              </span>
                            )}
                          </div>
                          <div className="text-right shrink-0">
                            <p className="font-bold text-lg" style={{ color: colors.priceText, fontFamily: 'var(--font-heading)' }}>
                              R$ {market.price.toFixed(2)}
                            </p>
                            <p className="text-xs" style={{ color: colors.text }}>
                              {market.unidade_comercial}
                            </p>
                          </div>
                        </div>
                        <div
                          className="flex items-start gap-2 px-4 py-2.5 text-xs"
                          style={{ borderTop: `1px solid ${colors.border}`, color: colors.text }}
                        >
                          <MapPin className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                          <p className="line-clamp-2">{market.market_address}</p>
                        </div>
                      </div>
                    );
                  }),
                );
              })()
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-3" style={{ backgroundColor: '#F8FAFC' }}>
                  <Package className="w-7 h-7" style={{ color: '#CBD5E1' }} />
                </div>
                <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                  Produto não encontrado em nenhum mercado
                </p>
                <p className="text-xs mt-1" style={{ color: '#94A3B8' }}>
                  Tente escanear mais cupons fiscais
                </p>
              </div>
            )}
          </div>
        </ModalWrapper>
      )}
    </div>
  );
};

export default ShoppingListPage;
