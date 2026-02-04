import React, { useState, useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { productService, marketService } from '../services/api';
import type { ProductSearchItem, Market, CompareResponse, BestMarketsResponse } from '../types';
import { 
  Search, Plus, Trash2, Store, 
  ArrowRightLeft, Check, X,
  TrendingDown, AlertCircle, ShoppingBasket,
  Package, MapPin, Award
} from 'lucide-react';

const MAX_MARKETS_FOR_COMPARISON = 5;

const ShoppingListPage: React.FC = () => {
  const { 
    shoppingList, addToShoppingList, removeFromShoppingList, clearShoppingList,
    selectedMarketIds, toggleMarketSelection
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
  
  // Best Places modal
  const [isBestPlacesOpen, setIsBestPlacesOpen] = useState(false);
  const [bestPlacesResult, setBestPlacesResult] = useState<BestMarketsResponse | null>(null);
  const [isFetchingBestPlaces, setIsFetchingBestPlaces] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductSearchItem | null>(null);
  
  // Fixed: Add debounce timer for search
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetchMarkets();
  }, []);

  const fetchMarkets = async () => {
    setIsLoadingMarkets(true);
    setMarketsError(null);
    try {
      const data = await marketService.getMarkets();
      setMarkets(data);
    } catch (error: any) {
      const message = (error as any).isBackendDown 
        ? (error as any).backendErrorMessage
        : error.response?.data?.error || error.message || "Falha ao buscar mercados";
      setMarketsError(message);
      console.error("Failed to fetch markets", error);
    } finally {
      setIsLoadingMarkets(false);
    }
  };

  // Fixed: Add debounce to search
  const handleSearch = (query: string) => {
    setSearchTerm(query);
    setSearchError(null);
    
    // Clear previous debounce timer
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }
    
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    // Set new debounce timer - wait 500ms before searching
    searchDebounceRef.current = setTimeout(() => {
      performSearch(query);
    }, 500);
  };

  const performSearch = async (query: string) => {
    setIsSearching(true);
    setSearchError(null);
    try {
      const data = await productService.searchProducts(query);
      setSearchResults(data.results);
    } catch (error: any) {
      // Fixed: Show error to user instead of silent fail
      const message = (error as any).isBackendDown 
        ? (error as any).backendErrorMessage
        : error.response?.data?.error || error.message || "Busca falhou";
      setSearchError(message);
      setSearchResults([]);
      console.error("Search failed", error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleToggleMarket = (marketId: string) => {
    if (!selectedMarketIds.includes(marketId) && selectedMarketIds.length >= MAX_MARKETS_FOR_COMPARISON) {
      setError(`Máximo de ${MAX_MARKETS_FOR_COMPARISON} mercados para comparação`);
      setTimeout(() => setError(null), 3000);
      return;
    }
    toggleMarketSelection(marketId);
  };

  const handleCompare = async () => {
    if (shoppingList.length === 0) {
      setError("Adicione produtos à sua lista primeiro");
      setTimeout(() => setError(null), 3000);
      return;
    }
    if (selectedMarketIds.length === 0) {
      setError("Selecione pelo menos um mercado");
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    setIsComparing(true);
    try {
      const result = await productService.compareProducts({
        products: shoppingList.map(p => ({ 
          ean: p.ean, 
          ncm: p.ncm, 
          product_name: p.product_name 
        })),
        market_ids: selectedMarketIds
      });
      setComparisonResult(result);
      setIsComparisonOpen(true);
    } catch (error: any) {
      // Fixed: Show error to user
      const message = (error as any).isBackendDown 
        ? (error as any).backendErrorMessage
        : error.response?.data?.error || error.message || "Comparação falhou";
      setError(message);
      setTimeout(() => setError(null), 3000);
      console.error("Comparison failed", error);
    } finally {
      setIsComparing(false);
    }
  };

  const handleProductClick = async (product: ProductSearchItem) => {
    setSelectedProduct(product);
    setIsBestPlacesOpen(true);
    setIsFetchingBestPlaces(true);
    
    try {
      const result = await productService.getBestMarketsForProduct({
        ean: product.ean,
        ncm: product.ncm,
        product_name: product.product_name
      }, 3);
      setBestPlacesResult(result);
    } catch (error: any) {
      const message = (error as any).isBackendDown 
        ? (error as any).backendErrorMessage
        : error.response?.data?.error || error.message || "Falha ao buscar melhores mercados";
      setError(message);
      setTimeout(() => setError(null), 3000);
      console.error("Best places fetch failed", error);
    } finally {
      setIsFetchingBestPlaces(false);
    }
  };

  return (
    <div className="p-4 md:p-6 pb-32">
      <div className="flex items-center justify-between mb-6 md:mb-8 gap-2">
        <h2 className="text-xl md:text-2xl font-bold">Lista de Compras</h2>
        <div className="flex gap-2">
          {shoppingList.length > 0 && (
            <button 
              onClick={clearShoppingList}
              className="p-2 text-red-500 hover:bg-red-50 rounded-xl transition-colors"
              title="Limpar Lista"
            >
              <Trash2 className="w-5 h-5 md:w-6 md:h-6" />
            </button>
          )}
          <button 
            onClick={() => setIsSearchModalOpen(true)}
            className="bg-blue-600 text-white p-2 px-3 md:px-4 rounded-xl font-medium text-sm md:text-base flex items-center gap-2 hover:bg-blue-700 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4 md:w-5 md:h-5" />
            <span className="hidden sm:inline">Adicionar Produto</span>
            <span className="sm:hidden">Adicionar</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-2xl text-sm font-medium flex items-center gap-2 animate-in fade-in slide-in-from-top-2 duration-300">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* Shopping List Items */}
      <div className="space-y-3">
        {shoppingList.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 border border-gray-100 flex flex-col items-center text-center">
            <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-4">
              <ShoppingBasket className="w-10 h-10 text-gray-300" />
            </div>
            <h3 className="text-lg font-bold text-gray-800">Sua lista está vazia</h3>
            <p className="text-gray-500 max-w-[200px]">Adicione produtos para comparar preços entre os mercados.</p>
          </div>
        ) : (
          shoppingList.map((product, idx) => (
            <div key={idx} className="bg-white p-3 md:p-4 rounded-2xl border border-gray-100 flex items-center justify-between gap-3 shadow-sm group">
              <button 
                onClick={() => handleProductClick(product)}
                className="flex items-center gap-3 flex-1 min-w-0 text-left hover:opacity-70 transition-opacity active:opacity-50"
              >
                {product.image_url ? (
                  <div className="w-12 h-12 md:w-10 md:h-10 bg-white rounded-lg border border-gray-100 overflow-hidden shrink-0 flex items-center justify-center">
                    <img 
                      src={product.image_url} 
                      alt={product.product_name}
                      className="w-full h-full object-contain"
                    />
                  </div>
                ) : (
                  <div className="w-12 h-12 md:w-10 md:h-10 bg-gray-50 rounded-lg flex items-center justify-center shrink-0 text-gray-300">
                    <Package className="w-5 h-5" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h4 className="font-bold text-sm md:text-base text-gray-800 truncate">{product.product_name}</h4>
                  <div className="flex flex-wrap items-center gap-2 mt-1">
                    <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-bold uppercase">
                      {product.unidade_comercial}
                    </span>
                    <span className="text-xs text-gray-400">
                      R$ {product.min_price?.toFixed(2) || '0.00'} - R$ {product.max_price?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                  <p className="text-[10px] text-blue-600 mt-1 font-medium">Toque para ver melhores lugares</p>
                </div>
              </button>
              <button 
                onClick={() => removeFromShoppingList(product)}
                className="text-gray-300 hover:text-red-500 active:text-red-700 transition-colors p-2 shrink-0"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Market Selector Bar */}
      <div className="fixed bottom-24 md:bottom-8 left-1/2 -translate-x-1/2 w-[95%] max-w-lg bg-white p-3 md:p-4 rounded-3xl shadow-2xl border border-gray-100 z-40 animate-in slide-in-from-bottom duration-500">
        <div className="flex items-center justify-between gap-3">
          <button 
            onClick={() => setIsMarketModalOpen(true)}
            className="flex-1 flex items-center gap-2 md:gap-3 text-left px-1"
          >
            <div className="w-9 h-9 md:w-10 md:h-10 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600 shrink-0">
              <Store className="w-5 h-5 md:w-6 md:h-6" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[9px] md:text-[10px] font-bold text-gray-400 uppercase tracking-widest">Mercados</p>
              <p className="font-bold text-sm md:text-base text-gray-800 truncate">
                {selectedMarketIds.length === 0 
                  ? 'Nenhum selecionado' 
                  : `${selectedMarketIds.length} de ${MAX_MARKETS_FOR_COMPARISON} selecionados`}
              </p>
            </div>
          </button>
          
          <button 
            onClick={handleCompare}
            disabled={shoppingList.length === 0 || selectedMarketIds.length === 0 || isComparing}
            className="bg-blue-600 disabled:bg-gray-100 text-white p-2.5 md:p-3 px-4 md:px-6 rounded-2xl font-bold text-sm md:text-base flex items-center gap-2 hover:bg-blue-700 transition-all active:scale-95 disabled:active:scale-100 shadow-lg shadow-blue-200 disabled:shadow-none"
          >
            {isComparing ? (
              <div className="w-4 h-4 md:w-5 md:h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <ArrowRightLeft className="w-4 h-4 md:w-5 md:h-5" />
            )}
            <span className="hidden sm:inline">Comparar</span>
          </button>
        </div>
      </div>

      {/* Search Modal */}
      {isSearchModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-end md:items-center justify-center p-0 md:p-6">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setIsSearchModalOpen(false)}></div>
          <div className="relative bg-white w-full max-w-xl h-[90vh] md:h-[80vh] rounded-t-3xl md:rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-300">
            <div className="p-6 border-b border-gray-100 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold">Adicionar Produto</h3>
                <button onClick={() => setIsSearchModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-full transition-colors"><X className="w-6 h-6" /></button>
              </div>
              
              {/* Fixed: Show search error */}
              {searchError && (
                <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  {searchError}
                </div>
              )}
              
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input 
                  autoFocus
                  type="text" 
                  placeholder="Buscar produtos por nome..."
                  className="w-full pl-10 pr-4 py-3 rounded-2xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50"
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="flex-1 overflow-auto p-4">
              {isSearching ? (
                <div className="flex justify-center py-12"><div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div></div>
              ) : (
                <div className="space-y-2">
                  {searchResults.map((product, idx) => (
                    <button 
                      key={idx}
                      onClick={() => {
                        addToShoppingList(product);
                        setIsSearchModalOpen(false);
                        setSearchTerm('');
                        setSearchResults([]);
                      }}
                      className="w-full text-left p-4 rounded-2xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50 transition-all flex items-center justify-between group"
                    >
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        {product.image_url ? (
                          <div className="w-10 h-10 bg-white rounded-lg border border-gray-100 overflow-hidden shrink-0 flex items-center justify-center">
                            <img 
                              src={product.image_url} 
                              alt={product.product_name}
                              className="w-full h-full object-contain"
                            />
                          </div>
                        ) : (
                          <div className="w-10 h-10 bg-gray-50 rounded-lg flex items-center justify-center shrink-0 text-gray-300">
                            <Package className="w-5 h-5" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-bold text-gray-800 truncate">{product.product_name}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <p className="text-xs text-gray-400 whitespace-nowrap">Encontrado em {product.markets_count} mercados</p>
                          </div>
                        </div>
                      </div>
                      <Plus className="w-5 h-5 text-gray-300 group-hover:text-blue-600" />
                    </button>
                  ))}
                  {searchTerm.length >= 2 && searchResults.length === 0 && !isSearching && !searchError && (
                    <div className="text-center py-12 text-gray-400 font-medium">Nenhum produto encontrado para "{searchTerm}"</div>
                  )}
                  {searchTerm.length < 2 && (
                    <div className="text-center py-12 text-gray-400 text-sm italic">Digite pelo menos 2 caracteres para buscar...</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Markets Selection Modal */}
      {isMarketModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-end md:items-center justify-center p-0 md:p-6">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setIsMarketModalOpen(false)}></div>
          <div className="relative bg-white w-full max-w-md h-[70vh] rounded-t-3xl md:rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-300">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold">Selecionar Mercados</h3>
                <p className="text-xs text-gray-500">Escolha até {MAX_MARKETS_FOR_COMPARISON} mercados para comparar</p>
              </div>
              <button onClick={() => setIsMarketModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-full transition-colors"><X className="w-6 h-6" /></button>
            </div>
            
            {/* Fixed: Show loading state and error */}
            {isLoadingMarkets ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-gray-500 text-sm">Carregando mercados...</p>
                </div>
              </div>
            ) : marketsError ? (
              <div className="flex-1 flex items-center justify-center p-6">
                <div className="text-center">
                  <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                  <p className="text-red-600 font-semibold mb-2">Falha ao carregar mercados</p>
                  <p className="text-gray-600 text-sm mb-4">{marketsError}</p>
                  <button 
                    onClick={fetchMarkets}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                  >
                    Tentar Novamente
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex-1 overflow-auto p-4 space-y-2">
                  {markets.map((market) => {
                    const isSelected = selectedMarketIds.includes(market.market_id);
                    return (
                      <button 
                        key={market.market_id}
                        onClick={() => handleToggleMarket(market.market_id)}
                        className={`w-full text-left p-4 rounded-2xl border transition-all flex items-center justify-between group ${
                          isSelected ? 'border-blue-200 bg-blue-50' : 'border-gray-100 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex-1 min-w-0">
                          <p className={`font-bold truncate ${isSelected ? 'text-blue-700' : 'text-gray-800'}`}>{market.name}</p>
                          <p className="text-xs text-gray-400 truncate">{market.address}</p>
                        </div>
                        <div className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all ${
                          isSelected ? 'bg-blue-600 border-blue-600 text-white' : 'border-gray-200 bg-white'
                        }`}>
                          {isSelected && <Check className="w-4 h-4" />}
                        </div>
                      </button>
                    );
                  })}
                  {markets.length === 0 && !isLoadingMarkets && (
                    <div className="text-center py-12 text-gray-400">
                      <p>Nenhum mercado encontrado</p>
                    </div>
                  )}
                </div>
                <div className="p-6 border-t border-gray-100 bg-gray-50">
                  <button 
                    onClick={() => setIsMarketModalOpen(false)}
                    className="w-full bg-gray-900 text-white py-4 rounded-2xl font-bold hover:bg-gray-800 transition-colors shadow-lg"
                  >
                    Pronto ({selectedMarketIds.length})
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Comparison Results Modal */}
      {isComparisonOpen && comparisonResult && (
        <div className="fixed inset-0 z-[110] flex items-end md:items-center justify-center p-0 md:p-6">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsComparisonOpen(false)}></div>
          <div className="relative bg-white w-full max-w-3xl h-[95vh] md:h-[90vh] rounded-t-3xl md:rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-400">
            <div className="p-4 md:p-6 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white z-10">
              <div>
                <h3 className="text-lg md:text-xl font-bold">Comparação de Preços</h3>
                <p className="text-xs text-gray-500 mt-1">{comparisonResult.comparison.length} produtos em {Object.keys(comparisonResult.markets).length} mercados</p>
              </div>
              <button onClick={() => setIsComparisonOpen(false)} className="p-2 hover:bg-gray-100 rounded-full transition-colors shrink-0">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-4 md:p-6">
              {/* Card-based comparison layout */}
              <div className="space-y-4">
                {comparisonResult.comparison.map((row, idx) => (
                  <div key={idx} className="bg-white rounded-3xl border border-gray-100 overflow-hidden shadow-sm">
                    {/* Product Header */}
                    <div className="bg-gray-50 p-4 border-b border-gray-100">
                      <div className="flex items-center gap-3">
                        {row.image_url ? (
                          <div className="w-12 h-12 bg-white rounded-lg border border-gray-100 overflow-hidden shrink-0 flex items-center justify-center">
                            <img 
                              src={row.image_url} 
                              alt={row.product_name}
                              className="w-full h-full object-contain"
                            />
                          </div>
                        ) : (
                          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center shrink-0 text-gray-400">
                            <Package className="w-6 h-6" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-bold text-gray-900 truncate">{row.product_name}</h4>
                          <p className="text-xs text-gray-500 mt-0.5">NCM: {row.ncm}</p>
                        </div>
                      </div>
                    </div>

                    {/* Market Prices */}
                    <div className="divide-y divide-gray-100">
                      {Object.entries(comparisonResult.markets).map(([mId, mName]) => {
                        const price = row.prices[mId];
                        const isMin = price !== null && price === row.min_price && !row.all_equal;
                        const isMax = price !== null && price === row.max_price && !row.all_equal;
                        
                        return (
                          <div key={mId} className="p-4 flex items-center justify-between gap-4 hover:bg-gray-50 transition-colors">
                            <div className="flex-1 min-w-0">
                              <p className="font-semibold text-gray-800 truncate text-sm">{mName}</p>
                            </div>
                            <div className="shrink-0">
                              {price == null ? (
                                <span className="text-gray-400 text-sm italic">N/D</span>
                              ) : (
                                <div className="flex flex-col items-end gap-1">
                                  <span className={`text-lg font-bold px-3 py-1.5 rounded-xl transition-all ${
                                    isMin ? 'bg-green-600 text-white shadow-md shadow-green-200' :
                                    isMax ? 'bg-red-50 text-red-700 border-2 border-red-200' :
                                    row.all_equal ? 'bg-blue-50 text-blue-700 border-2 border-blue-200' :
                                    'text-gray-800 bg-gray-50'
                                  }`}>
                                    R$ {price.toFixed(2)}
                                  </span>
                                  {isMin && (
                                    <span className="text-[9px] font-bold text-green-700 bg-green-100 px-2 py-0.5 rounded-full uppercase tracking-wider">
                                      Melhor Preço
                                    </span>
                                  )}
                                  {isMax && !row.all_equal && (
                                    <span className="text-[9px] font-bold text-red-700 bg-red-100 px-2 py-0.5 rounded-full uppercase tracking-wider">
                                      Mais Caro
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-8 grid grid-cols-1 gap-4">
                <div className="bg-blue-50 p-5 rounded-2xl border border-blue-100 flex items-start gap-3">
                  <div className="p-2.5 bg-blue-600 rounded-xl text-white shadow-lg shadow-blue-100 shrink-0"><TrendingDown className="w-5 h-5" /></div>
                  <div>
                    <h4 className="font-bold text-blue-900 mb-1 text-sm">Análise de Preços</h4>
                    <p className="text-xs text-blue-700 leading-relaxed">O destaque em verde indica o menor preço absoluto encontrado para cada produto entre os mercados selecionados.</p>
                  </div>
                </div>
                <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100 flex items-start gap-3">
                  <div className="p-2.5 bg-gray-300 rounded-xl text-gray-600 shrink-0"><AlertCircle className="w-5 h-5" /></div>
                  <div>
                    <h4 className="font-bold text-gray-900 mb-1 text-sm">Disponibilidade</h4>
                    <p className="text-xs text-gray-600 leading-relaxed">Resultados "N/D" indicam que o produto não foi encontrado neste mercado ou não teve cupom escaneado recentemente.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Best Places Modal */}
      {isBestPlacesOpen && selectedProduct && (
        <div className="fixed inset-0 z-[120] flex items-end md:items-center justify-center p-0 md:p-6">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsBestPlacesOpen(false)}></div>
          <div className="relative bg-white w-full max-w-lg h-auto max-h-[85vh] rounded-t-3xl md:rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-400">
            <div className="p-6 border-b border-gray-100 sticky top-0 bg-white z-10">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xl font-bold">Melhores Lugares</h3>
                <button onClick={() => setIsBestPlacesOpen(false)} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                  <X className="w-6 h-6" />
                </button>
              </div>
              <div className="flex items-center gap-3 mt-4">
                {selectedProduct.image_url ? (
                  <div className="w-12 h-12 bg-white rounded-lg border border-gray-100 overflow-hidden shrink-0 flex items-center justify-center">
                    <img 
                      src={selectedProduct.image_url} 
                      alt={selectedProduct.product_name}
                      className="w-full h-full object-contain"
                    />
                  </div>
                ) : (
                  <div className="w-12 h-12 bg-gray-50 rounded-lg flex items-center justify-center shrink-0 text-gray-300">
                    <Package className="w-6 h-6" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-gray-800 truncate">{selectedProduct.product_name}</p>
                  <p className="text-xs text-gray-400">Top 3 mercados com menor preço</p>
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-6">
              {isFetchingBestPlaces ? (
                <div className="flex justify-center py-12">
                  <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : bestPlacesResult && bestPlacesResult.best_markets.length > 0 ? (
                <div className="space-y-3">
                  {(() => {
                    // Group markets by price and assign rank based on unique prices
                    const priceGroups = bestPlacesResult.best_markets.reduce((acc, market) => {
                      const priceKey = market.price.toFixed(2);
                      if (!acc[priceKey]) {
                        acc[priceKey] = [];
                      }
                      acc[priceKey].push(market);
                      return acc;
                    }, {} as Record<string, typeof bestPlacesResult.best_markets>);
                    
                    const uniquePrices = Object.keys(priceGroups).sort((a, b) => parseFloat(a) - parseFloat(b));
                    
                    return uniquePrices.flatMap((priceKey, priceRank) => 
                      priceGroups[priceKey].map((market, marketIdx) => {
                        const isFirstInGroup = marketIdx === 0;
                        const groupSize = priceGroups[priceKey].length;
                        const hasTie = groupSize > 1;
                        
                        // Color scheme based on rank
                        const colors = {
                          bg: priceRank === 0 ? 'bg-green-50' : priceRank === 1 ? 'bg-blue-50' : 'bg-orange-50',
                          border: priceRank === 0 ? 'border-green-200' : priceRank === 1 ? 'border-blue-200' : 'border-orange-200',
                          iconBg: priceRank === 0 ? 'bg-green-600' : priceRank === 1 ? 'bg-blue-600' : 'bg-orange-600',
                          textTitle: priceRank === 0 ? 'text-green-900' : priceRank === 1 ? 'text-blue-900' : 'text-orange-900',
                          textPrice: priceRank === 0 ? 'text-green-700' : priceRank === 1 ? 'text-blue-700' : 'text-orange-700',
                          badge: priceRank === 0 ? 'text-green-700 bg-green-100' : priceRank === 1 ? 'text-blue-700 bg-blue-100' : 'text-orange-700 bg-orange-100',
                        };
                        
                        return (
                          <div 
                            key={market.market_id} 
                            className={`p-5 rounded-2xl border-2 transition-all ${colors.bg} ${colors.border}`}
                          >
                            <div className="flex items-start justify-between gap-4 mb-3">
                              <div className="flex items-center gap-3 flex-1 min-w-0">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${colors.iconBg} text-white`}>
                                  {priceRank === 0 ? (
                                    <Award className="w-6 h-6" />
                                  ) : (
                                    <span className="font-bold text-lg">{priceRank + 1}</span>
                                  )}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <h4 className={`font-bold text-lg truncate ${colors.textTitle}`}>
                                    {market.market_name}
                                  </h4>
                                  {isFirstInGroup && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {priceRank === 0 && (
                                        <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${colors.badge}`}>
                                          {hasTie ? `Melhor Preço (${groupSize} mercados)` : 'Melhor Preço'}
                                        </span>
                                      )}
                                      {priceRank > 0 && hasTie && (
                                        <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${colors.badge}`}>
                                          Empate - {groupSize} mercados
                                        </span>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                              <div className="text-right">
                                <p className={`text-2xl font-bold ${colors.textPrice}`}>
                                  R$ {market.price.toFixed(2)}
                                </p>
                                <p className="text-[10px] text-gray-500 uppercase font-bold">{market.unidade_comercial}</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-2 text-sm text-gray-600 pt-3 border-t border-gray-200">
                              <MapPin className="w-4 h-4 mt-0.5 shrink-0" />
                              <p className="line-clamp-2 leading-snug">{market.market_address}</p>
                            </div>
                          </div>
                        );
                      })
                    );
                  })()}
                  {bestPlacesResult.total_markets_found > bestPlacesResult.best_markets.length && (
                    <p className="text-center text-xs text-gray-500 pt-2">
                      Encontrado em {bestPlacesResult.total_markets_found} mercados no total
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Package className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p className="text-gray-500 font-medium">Produto não encontrado em nenhum mercado</p>
                  <p className="text-sm text-gray-400 mt-2">Tente escanear mais cupons fiscais</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShoppingListPage;
