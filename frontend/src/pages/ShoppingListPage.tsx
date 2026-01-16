import React, { useState, useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { productService, marketService } from '../services/api';
import type { ProductSearchItem, Market, CompareResponse } from '../types';
import { 
  Search, Plus, Trash2, Store, 
  ArrowRightLeft, Check, X,
  TrendingDown, AlertCircle, ShoppingBasket
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
        : error.response?.data?.error || error.message || "Failed to fetch markets";
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
        : error.response?.data?.error || error.message || "Search failed";
      setSearchError(message);
      setSearchResults([]);
      console.error("Search failed", error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleToggleMarket = (marketId: string) => {
    if (!selectedMarketIds.includes(marketId) && selectedMarketIds.length >= MAX_MARKETS_FOR_COMPARISON) {
      setError(`Maximum of ${MAX_MARKETS_FOR_COMPARISON} markets for comparison`);
      setTimeout(() => setError(null), 3000);
      return;
    }
    toggleMarketSelection(marketId);
  };

  const handleCompare = async () => {
    if (shoppingList.length === 0) {
      setError("Add products to your list first");
      setTimeout(() => setError(null), 3000);
      return;
    }
    if (selectedMarketIds.length === 0) {
      setError("Select at least one market");
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
        : error.response?.data?.error || error.message || "Comparison failed";
      setError(message);
      setTimeout(() => setError(null), 3000);
      console.error("Comparison failed", error);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="p-6 pb-32">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-bold">Shopping List</h2>
        <div className="flex gap-2">
          {shoppingList.length > 0 && (
            <button 
              onClick={clearShoppingList}
              className="p-2 text-red-500 hover:bg-red-50 rounded-xl transition-colors"
              title="Clear List"
            >
              <Trash2 className="w-6 h-6" />
            </button>
          )}
          <button 
            onClick={() => setIsSearchModalOpen(true)}
            className="bg-blue-600 text-white p-2 px-4 rounded-xl font-medium flex items-center gap-2 hover:bg-blue-700 transition-colors shadow-sm"
          >
            <Plus className="w-5 h-5" />
            Add Product
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
            <h3 className="text-lg font-bold text-gray-800">Your list is empty</h3>
            <p className="text-gray-500 max-w-[200px]">Add products to compare prices across markets.</p>
          </div>
        ) : (
          shoppingList.map((product, idx) => (
            <div key={idx} className="bg-white p-4 rounded-2xl border border-gray-100 flex items-center justify-between gap-4 shadow-sm group">
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
                  <h4 className="font-bold text-gray-800 truncate">{product.product_name}</h4>
                  <div className="flex flex-wrap items-center gap-2 mt-1">
                    <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-bold uppercase">
                      {product.unidade_comercial}
                    </span>
                    <span className="text-xs text-gray-400">
                      Est. R$ {product.min_price?.toFixed(2) || '0.00'} - R$ {product.max_price?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                </div>
              </div>
              <button 
                onClick={() => removeFromShoppingList(product)}
                className="text-gray-300 hover:text-red-500 transition-colors p-2"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Market Selector Bar */}
      <div className="fixed bottom-24 md:bottom-8 left-1/2 -translate-x-1/2 w-[95%] max-w-lg bg-white p-4 rounded-3xl shadow-2xl border border-gray-100 z-40 animate-in slide-in-from-bottom duration-500">
        <div className="flex items-center justify-between gap-4">
          <button 
            onClick={() => setIsMarketModalOpen(true)}
            className="flex-1 flex items-center gap-3 text-left px-2"
          >
            <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600 shrink-0">
              <Store className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Markets</p>
              <p className="font-bold text-gray-800 truncate">
                {selectedMarketIds.length === 0 
                  ? 'None selected' 
                  : `${selectedMarketIds.length} of ${MAX_MARKETS_FOR_COMPARISON} selected`}
              </p>
            </div>
          </button>
          
          <button 
            onClick={handleCompare}
            disabled={shoppingList.length === 0 || selectedMarketIds.length === 0 || isComparing}
            className="bg-blue-600 disabled:bg-gray-100 text-white p-3 px-6 rounded-2xl font-bold flex items-center gap-2 hover:bg-blue-700 transition-all active:scale-95 disabled:active:scale-100 shadow-lg shadow-blue-200"
          >
            {isComparing ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <ArrowRightLeft className="w-5 h-5" />
            )}
            Compare
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
                <h3 className="text-xl font-bold">Add Product</h3>
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
                  placeholder="Search products by name..."
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
                            <p className="text-xs text-gray-400 whitespace-nowrap">Found in {product.markets_count} markets</p>
                          </div>
                        </div>
                      </div>
                      <Plus className="w-5 h-5 text-gray-300 group-hover:text-blue-600" />
                    </button>
                  ))}
                  {searchTerm.length >= 2 && searchResults.length === 0 && !isSearching && !searchError && (
                    <div className="text-center py-12 text-gray-400 font-medium">No products found matching "{searchTerm}"</div>
                  )}
                  {searchTerm.length < 2 && (
                    <div className="text-center py-12 text-gray-400 text-sm italic">Type at least 2 characters to search...</div>
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
                <h3 className="text-xl font-bold">Select Markets</h3>
                <p className="text-xs text-gray-500">Pick up to {MAX_MARKETS_FOR_COMPARISON} markets to compare</p>
              </div>
              <button onClick={() => setIsMarketModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-full transition-colors"><X className="w-6 h-6" /></button>
            </div>
            
            {/* Fixed: Show loading state and error */}
            {isLoadingMarkets ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-gray-500 text-sm">Loading markets...</p>
                </div>
              </div>
            ) : marketsError ? (
              <div className="flex-1 flex items-center justify-center p-6">
                <div className="text-center">
                  <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                  <p className="text-red-600 font-semibold mb-2">Failed to load markets</p>
                  <p className="text-gray-600 text-sm mb-4">{marketsError}</p>
                  <button 
                    onClick={fetchMarkets}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                  >
                    Retry
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
                      <p>No markets found</p>
                    </div>
                  )}
                </div>
                <div className="p-6 border-t border-gray-100 bg-gray-50">
                  <button 
                    onClick={() => setIsMarketModalOpen(false)}
                    className="w-full bg-gray-900 text-white py-4 rounded-2xl font-bold hover:bg-gray-800 transition-colors shadow-lg"
                  >
                    Done ({selectedMarketIds.length})
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
          <div className="relative bg-white w-full max-w-4xl h-[95vh] md:h-[90vh] rounded-t-3xl md:rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-400">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white z-10">
              <h3 className="text-xl font-bold">Price Comparison</h3>
              <button onClick={() => setIsComparisonOpen(false)} className="p-2 hover:bg-gray-100 rounded-full transition-colors"><X className="w-6 h-6" /></button>
            </div>

            <div className="flex-1 overflow-auto p-4 md:p-6">
              <div className="inline-block min-w-full align-middle">
                <div className="overflow-hidden border border-gray-100 rounded-3xl">
                  <table className="min-w-full divide-y divide-gray-100">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest sticky left-0 bg-gray-50 z-10">Product</th>
                        {Object.entries(comparisonResult.markets).map(([id, name]) => (
                          <th key={id} className="px-6 py-4 text-center text-xs font-bold text-gray-400 uppercase tracking-widest">{name}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                      {comparisonResult.comparison.map((row, idx) => (
                        <tr key={idx} className="hover:bg-gray-50 transition-colors group">
                          <td className="px-6 py-4 sticky left-0 bg-white group-hover:bg-gray-50 z-10 border-r border-gray-50">
                            <div className="flex items-center gap-3">
                              {row.image_url ? (
                                <div className="w-10 h-10 bg-white rounded-lg border border-gray-100 overflow-hidden shrink-0 flex items-center justify-center">
                                  <img 
                                    src={row.image_url} 
                                    alt={row.product_name}
                                    className="w-full h-full object-contain"
                                  />
                                </div>
                              ) : (
                                <div className="w-10 h-10 bg-gray-50 rounded-lg flex items-center justify-center shrink-0 text-gray-300">
                                  <Package className="w-5 h-5" />
                                </div>
                              )}
                              <div className="min-w-0">
                                <p className="text-sm font-bold text-gray-800 min-w-[150px] leading-tight truncate">{row.product_name}</p>
                                <p className="text-[10px] text-gray-400 mt-1">NCM: {row.ncm}</p>
                              </div>
                            </div>
                          </td>
                          {Object.keys(comparisonResult.markets).map((mId) => {
                            const price = row.prices[mId];
                            const isMin = price !== null && price === row.min_price && !row.all_equal;
                            const isMax = price !== null && price === row.max_price && !row.all_equal;
                            
                            return (
                              <td key={mId} className="px-6 py-4 text-center whitespace-nowrap">
                                {price == null ? (
                                  <span className="text-gray-300 text-xs italic">N/A</span>
                                ) : (
                                  <div className="flex flex-col items-center">
                                    <span className={`text-sm font-bold px-3 py-1 rounded-lg transition-all ${
                                      isMin ? 'bg-green-600 text-white shadow-md shadow-green-100' :
                                      isMax ? 'bg-red-50 text-red-600 border border-red-100' :
                                      row.all_equal ? 'bg-blue-50 text-blue-600 border border-blue-100' :
                                      'text-gray-700'
                                    }`}>
                                      R$ {price.toFixed(2)}
                                    </span>
                                    {isMin && <span className="text-[8px] font-bold text-green-600 uppercase mt-1 tracking-tighter">Best Price</span>}
                                  </div>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              
              <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-blue-50 p-6 rounded-3xl border border-blue-100 flex items-start gap-4">
                  <div className="p-3 bg-blue-600 rounded-2xl text-white shadow-lg shadow-blue-100"><TrendingDown className="w-6 h-6" /></div>
                  <div>
                    <h4 className="font-bold text-blue-900 mb-1">Price Analysis</h4>
                    <p className="text-sm text-blue-700 leading-relaxed">Solid green indicates the absolute lowest price found for each specific product among chosen markets.</p>
                  </div>
                </div>
                <div className="bg-gray-50 p-6 rounded-3xl border border-gray-100 flex items-start gap-4">
                  <div className="p-3 bg-gray-200 rounded-2xl text-gray-500"><AlertCircle className="w-6 h-6" /></div>
                  <div>
                    <h4 className="font-bold text-gray-900 mb-1">Market Coverage</h4>
                    <p className="text-sm text-gray-500 leading-relaxed">"N/A" results suggest that this market doesn't carry this product or hasn't had a receipt scanned for it recently.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShoppingListPage;
