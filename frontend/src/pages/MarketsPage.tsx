import React, { useEffect, useState, useMemo } from 'react';
import { marketService } from '../services/api';
import type { Market, Product } from '../types';
import { Store, ChevronRight, Search, Package, MapPin, X } from 'lucide-react';

const MarketsPage: React.FC = () => {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);
  const [marketProducts, setMarketProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [productSearchTerm, setProductSearchTerm] = useState('');

  useEffect(() => {
    fetchMarkets();
  }, []);

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
    return marketProducts.filter(
      p =>
        p.product_name.toLowerCase().includes(query) ||
        p.ncm.toLowerCase().includes(query),
    );
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
              className="text-left rounded-xl p-4 cursor-pointer transition-all duration-200 group"
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-sm)',
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.boxShadow = 'var(--shadow-md)';
                (e.currentTarget as HTMLElement).style.borderColor = 'var(--color-primary)';
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.boxShadow = 'var(--shadow-sm)';
                (e.currentTarget as HTMLElement).style.borderColor = 'var(--color-border)';
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className="flex items-center justify-center w-10 h-10 rounded-xl transition-colors duration-200"
                  style={{ backgroundColor: '#EFF6FF' }}
                >
                  <Store className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
                </div>
                <ChevronRight
                  className="w-4 h-4 mt-1 transition-colors duration-200"
                  style={{ color: '#CBD5E1' }}
                />
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

      {/* Market Products Modal */}
      {selectedMarket && (
        <div className="fixed inset-0 z-[100] flex items-end md:items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setSelectedMarket(null)}
          />

          <div
            className="relative w-full max-w-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-300"
            style={{
              backgroundColor: 'var(--color-surface)',
              borderRadius: '20px 20px 0 0',
              maxHeight: '90vh',
              boxShadow: 'var(--shadow-xl)',
            }}
          >
            {/* Modal Header */}
            <div
              className="px-5 py-4 sticky top-0 z-10 space-y-3"
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
                      className="font-bold text-base leading-tight truncate"
                      style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
                    >
                      {selectedMarket.name}
                    </h3>
                    <p
                      className="text-xs mt-0.5 truncate"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      {selectedMarket.address}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedMarket(null)}
                  className="shrink-0 flex items-center justify-center w-8 h-8 rounded-full cursor-pointer transition-all duration-200 hover:opacity-80"
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
                  placeholder="Buscar produtos por nome ou NCM..."
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
            <div className="flex-1 overflow-auto p-4">
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
                    <div
                      key={product.id}
                      className="flex items-center gap-3 p-3 rounded-xl"
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
                          className="text-sm font-semibold truncate leading-tight"
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
                          <span className="text-xs" style={{ color: '#94A3B8' }}>
                            NCM {product.ncm}
                          </span>
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
                    </div>
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
    </div>
  );
};

export default MarketsPage;
