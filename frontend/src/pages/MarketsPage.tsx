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
      console.error("Failed to fetch markets", error);
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
      console.error("Failed to fetch products", error);
    } finally {
      setLoadingProducts(false);
    }
  };

  const filteredMarkets = markets.filter(m => 
    m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.address.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredProducts = useMemo(() => {
    if (!productSearchTerm.trim()) return marketProducts;
    const query = productSearchTerm.toLowerCase();
    return marketProducts.filter(p => {
      return p.product_name.toLowerCase().includes(query) || 
             p.ncm.toLowerCase().includes(query);
    });
  }, [marketProducts, productSearchTerm]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold">Available Markets</h2>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input 
            type="text" 
            placeholder="Search markets..."
            className="pl-10 pr-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white md:w-64"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredMarkets.map((market) => (
            <button
              key={market.market_id}
              onClick={() => handleMarketClick(market)}
              className="bg-white p-5 rounded-3xl shadow-sm border border-gray-100 hover:border-blue-200 hover:shadow-md transition-all text-left group"
            >
              <div className="flex items-start justify-between">
                <div className="p-3 bg-blue-50 rounded-2xl text-blue-600 mb-4 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                  <Store className="w-6 h-6" />
                </div>
                <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-blue-600 transition-colors" />
              </div>
              <h3 className="font-bold text-lg leading-tight mb-2 truncate w-full">{market.name}</h3>
              <p className="text-sm text-gray-500 flex items-start gap-1 line-clamp-2">
                <MapPin className="w-4 h-4 mt-0.5 shrink-0" />
                {market.address}
              </p>
            </button>
          ))}
          {filteredMarkets.length === 0 && (
            <div className="col-span-full text-center py-20 text-gray-400">
              <Store className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No markets found matching your search.</p>
            </div>
          )}
        </div>
      )}

      {/* Product List Modal/Overlay */}
      {selectedMarket && (
        <div className="fixed inset-0 z-[100] flex items-end md:items-center justify-center p-0 md:p-6">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setSelectedMarket(null)}></div>
          <div className="relative bg-white w-full max-w-2xl h-[90vh] md:h-[80vh] rounded-t-3xl md:rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-300">
            <div className="p-6 border-b border-gray-100 space-y-4 sticky top-0 bg-white z-10">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold">{selectedMarket.name}</h3>
                  <p className="text-sm text-gray-500">{selectedMarket.address}</p>
                </div>
                <button 
                  onClick={() => setSelectedMarket(null)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input 
                  type="text" 
                  placeholder="Search products by name or NCM..."
                  className="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50"
                  value={productSearchTerm}
                  onChange={(e) => setProductSearchTerm(e.target.value)}
                />
              </div>
            </div>

            <div className="flex-1 overflow-auto p-6">
              {loadingProducts ? (
                <div className="flex justify-center py-20">
                  <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredProducts.map((product) => (
                    <div key={product.id} className="p-4 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        {product.image_url ? (
                          <div className="w-12 h-12 bg-white rounded-xl border border-gray-100 overflow-hidden shrink-0 flex items-center justify-center">
                            <img 
                              src={product.image_url} 
                              alt={product.product_name}
                              className="w-full h-full object-contain"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = 'https://placehold.co/100x100?text=No+Image';
                              }}
                            />
                          </div>
                        ) : (
                          <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center shrink-0 text-gray-400">
                            <Package className="w-6 h-6" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm leading-tight mb-1">{product.product_name}</p>
                          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400">
                            <span className="bg-white px-2 py-0.5 rounded border border-gray-100">{product.unidade_comercial}</span>
                            <span className="flex items-center gap-1">
                              NCM: {product.ncm}
                            </span>
                            {product.ean && product.ean !== 'SEM GTIN' && (
                              <span>EAN: {product.ean}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-blue-600">R$ {(product.price || 0).toFixed(2)}</p>
                      </div>
                    </div>
                  ))}
                  {filteredProducts.length === 0 && (
                    <div className="text-center py-20 text-gray-400">
                      <Package className="w-12 h-12 mx-auto mb-4 opacity-20" />
                      <p>No products found.</p>
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

