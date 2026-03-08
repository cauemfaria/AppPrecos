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

const modalBase: React.CSSProperties = {
  backgroundColor: 'var(--color-surface)',
  boxShadow: 'var(--shadow-xl)',
};

const ModalWrapper: React.FC<{
  onClose: () => void;
  children: React.ReactNode;
  zIndex?: number;
  maxWidth?: string;
  height?: string;
}> = ({ onClose, children, zIndex = 100, maxWidth = '520px', height = '90vh' }) => (
  <div
    className="fixed inset-0 flex items-end md:items-center justify-center"
    style={{ zIndex }}
  >
    <div
      className="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-pointer"
      onClick={onClose}
    />
    <div
      className="relative w-full flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-300"
      style={{
        ...modalBase,
        maxWidth,
        maxHeight: height,
        borderRadius: '20px 20px 0 0',
        borderTopLeftRadius: 20,
        borderTopRightRadius: 20,
      }}
    >
      {children}
    </div>
  </div>
);

const ModalHeader: React.FC<{
  title: string;
  subtitle?: string;
  onClose: () => void;
  children?: React.ReactNode;
}> = ({ title, subtitle, onClose, children }) => (
  <div
    className="px-5 py-4 sticky top-0 z-10 space-y-3"
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
        className="flex items-center justify-center w-8 h-8 rounded-full cursor-pointer transition-all duration-200 hover:opacity-80 shrink-0"
        style={{ backgroundColor: '#F1F5F9' }}
      >
        <X className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
      </button>
    </div>
    {children}
  </div>
);

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

  const [isComparisonOpen, setIsComparisonOpen] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<CompareResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [isBestPlacesOpen, setIsBestPlacesOpen] = useState(false);
  const [bestPlacesResult, setBestPlacesResult] = useState<BestMarketsResponse | null>(null);
  const [isFetchingBestPlaces, setIsFetchingBestPlaces] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductSearchItem | null>(null);

  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { fetchMarkets(); }, []);

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
      setError(`Máximo de ${MAX_MARKETS_FOR_COMPARISON} mercados`);
      setTimeout(() => setError(null), 3000);
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
      className="p-4 pb-40"
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
              className="flex items-center justify-center w-9 h-9 rounded-xl cursor-pointer transition-all duration-200 hover:opacity-80"
              style={{ backgroundColor: '#FEF2F2' }}
              title="Limpar lista"
            >
              <Trash2 className="w-4 h-4" style={{ color: '#EF4444' }} />
            </button>
          )}
          <button
            onClick={() => setIsSearchModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-semibold text-sm cursor-pointer transition-all duration-200 active:scale-[0.98]"
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
                className="flex items-center gap-3 flex-1 min-w-0 text-left cursor-pointer"
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
                    className="text-sm font-semibold truncate"
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
                className="shrink-0 flex items-center justify-center w-8 h-8 rounded-lg cursor-pointer transition-all duration-200 hover:opacity-80"
                style={{ backgroundColor: '#FEF2F2' }}
              >
                <Trash2 className="w-4 h-4" style={{ color: '#EF4444' }} />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Floating Market Selector Bar */}
      <div
        className="fixed left-1/2 -translate-x-1/2 w-[calc(100%-2rem)] max-w-lg z-40"
        style={{ bottom: 'calc(80px + env(safe-area-inset-bottom, 0px))' }}
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
            className="flex items-center gap-2.5 flex-1 min-w-0 cursor-pointer text-left"
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
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm cursor-pointer transition-all duration-200 active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed"
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
        <ModalWrapper onClose={() => setIsSearchModalOpen(false)} zIndex={100}>
          <ModalHeader title="Adicionar Produto" onClose={() => setIsSearchModalOpen(false)}>
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
                autoFocus
                type="text"
                placeholder="Buscar produtos por nome..."
                value={searchTerm}
                onChange={e => handleSearch(e.target.value)}
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
          </ModalHeader>

          <div className="flex-1 overflow-auto p-4 space-y-2">
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
                    setIsSearchModalOpen(false);
                    setSearchTerm('');
                    setSearchResults([]);
                  }}
                  className="w-full text-left flex items-center justify-between gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200"
                  style={{
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-surface)',
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.backgroundColor = '#EFF6FF';
                    (e.currentTarget as HTMLElement).style.borderColor = 'var(--color-primary)';
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--color-surface)';
                    (e.currentTarget as HTMLElement).style.borderColor = 'var(--color-border)';
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
                      <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text)' }}>
                        {product.product_name}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
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
        <ModalWrapper onClose={() => setIsMarketModalOpen(false)} zIndex={100} maxWidth="440px" height="70vh">
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
                className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer"
                style={{ backgroundColor: 'var(--color-primary)', color: 'white' }}
              >
                Tentar Novamente
              </button>
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-auto p-4 space-y-2">
                {markets.map(market => {
                  const isSelected = selectedMarketIds.includes(market.market_id);
                  return (
                    <button
                      key={market.market_id}
                      onClick={() => handleToggleMarket(market.market_id)}
                      className="w-full text-left flex items-center justify-between gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200"
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
                        className="flex items-center justify-center w-6 h-6 rounded-lg shrink-0 transition-all duration-200"
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
                className="p-4"
                style={{ borderTop: '1px solid var(--color-border)', backgroundColor: '#F8FAFC' }}
              >
                <button
                  onClick={() => setIsMarketModalOpen(false)}
                  className="w-full py-3 rounded-xl font-bold text-sm cursor-pointer transition-all duration-200 active:scale-[0.98]"
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
      {isComparisonOpen && comparisonResult && (
        <ModalWrapper onClose={() => setIsComparisonOpen(false)} zIndex={110} maxWidth="720px" height="95vh">
          <ModalHeader
            title="Comparação de Preços"
            subtitle={`${comparisonResult.comparison.length} produtos · ${Object.keys(comparisonResult.markets).length} mercados`}
            onClose={() => setIsComparisonOpen(false)}
          />
          <div className="flex-1 overflow-auto p-4 space-y-3">
            {comparisonResult.comparison.map((row, idx) => (
              <div
                key={idx}
                className="overflow-hidden rounded-xl"
                style={{ border: '1px solid var(--color-border)', backgroundColor: 'var(--color-surface)' }}
              >
                {/* Product header */}
                <div
                  className="flex items-center gap-3 p-3"
                  style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid var(--color-border)' }}
                >
                  {row.image_url ? (
                    <div className="w-10 h-10 rounded-lg overflow-hidden shrink-0" style={{ border: '1px solid var(--color-border)' }}>
                      <img src={row.image_url} alt={row.product_name} className="w-full h-full object-contain" />
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded-lg shrink-0 flex items-center justify-center" style={{ backgroundColor: '#F1F5F9' }}>
                      <Package className="w-5 h-5" style={{ color: '#CBD5E1' }} />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold truncate" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-heading)' }}>
                      {row.product_name}
                    </p>
                    <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>NCM {row.ncm}</p>
                  </div>
                </div>
                {/* Prices */}
                <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
                  {Object.entries(comparisonResult.markets).map(([mId, mName]) => {
                    const price = row.prices[mId];
                    const isMin = price !== null && price === row.min_price && !row.all_equal;
                    const isMax = price !== null && price === row.max_price && !row.all_equal;
                    return (
                      <div key={mId} className="flex items-center justify-between px-4 py-3">
                        <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>{mName}</p>
                        {price == null ? (
                          <span className="text-xs italic" style={{ color: '#94A3B8' }}>N/D</span>
                        ) : (
                          <div className="flex flex-col items-end gap-0.5">
                            <span
                              className="text-sm font-bold px-2.5 py-1 rounded-lg"
                              style={{
                                backgroundColor: isMin ? '#16A34A' : isMax ? '#FEF2F2' : '#F8FAFC',
                                color: isMin ? 'white' : isMax ? '#DC2626' : 'var(--color-text)',
                                border: isMax ? '1px solid #FECACA' : 'none',
                              }}
                            >
                              R$ {price.toFixed(2)}
                            </span>
                            {isMin && (
                              <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full" style={{ backgroundColor: '#DCFCE7', color: '#166534' }}>
                                Melhor Preço
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}

            {/* Info cards */}
            <div className="space-y-2 mt-2">
              <div
                className="flex items-start gap-3 p-3 rounded-xl"
                style={{ backgroundColor: '#EFF6FF', border: '1px solid #BFDBFE' }}
              >
                <TrendingDown className="w-4 h-4 mt-0.5 shrink-0" style={{ color: 'var(--color-primary)' }} />
                <p className="text-xs" style={{ color: '#1E40AF' }}>
                  O destaque em verde indica o menor preço absoluto por produto.
                </p>
              </div>
              <div
                className="flex items-start gap-3 p-3 rounded-xl"
                style={{ backgroundColor: '#F8FAFC', border: '1px solid var(--color-border)' }}
              >
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#94A3B8' }} />
                <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                  "N/D" indica produto não encontrado ou sem cupom recente neste mercado.
                </p>
              </div>
            </div>
          </div>
        </ModalWrapper>
      )}

      {/* === MODAL 4: Best Places === */}
      {isBestPlacesOpen && selectedProduct && (
        <ModalWrapper onClose={() => setIsBestPlacesOpen(false)} zIndex={120} maxWidth="500px" height="85vh">
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
              <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text)' }}>
                {selectedProduct.product_name}
              </p>
            </div>
          </ModalHeader>

          <div className="flex-1 overflow-auto p-4 space-y-3">
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
