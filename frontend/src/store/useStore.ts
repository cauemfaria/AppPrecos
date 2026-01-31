import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ProductSearchItem, ProcessingItem } from '../types';

interface AppState {
  // Shopping List
  shoppingList: ProductSearchItem[];
  addToShoppingList: (product: ProductSearchItem) => void;
  removeFromShoppingList: (product: ProductSearchItem) => void;
  clearShoppingList: () => void;

  // Market Selection
  selectedMarketIds: string[];
  toggleMarketSelection: (marketId: string) => void;
  clearMarketSelection: () => void;

  // Search
  searchResults: ProductSearchItem[];
  setSearchResults: (results: ProductSearchItem[]) => void;
  clearSearchResults: () => void;
  
  // Search loading
  isSearching: boolean;
  setIsSearching: (loading: boolean) => void;

  // NFCe Processing Queue
  processingQueue: ProcessingItem[];
  addToProcessingQueue: (item: ProcessingItem) => void;
  updateProcessingItem: (recordId: number, updates: Partial<ProcessingItem>) => void;
  removeFromProcessingQueue: (recordId: number) => void;
  setProcessingQueue: (items: ProcessingItem[]) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Shopping List
      shoppingList: [],
      addToShoppingList: (product) => 
        set((state) => {
          // Fixed: Check for duplicate atomically within set
          const exists = state.shoppingList.some(p => p.ean === product.ean && p.product_name === product.product_name);
          return {
            shoppingList: exists ? state.shoppingList : [...state.shoppingList, product]
          };
        }),
      removeFromShoppingList: (product) =>
        set((state) => ({
          shoppingList: state.shoppingList.filter(p => 
            !(p.ean === product.ean && p.product_name === product.product_name)
          )
        })),
      clearShoppingList: () => set({ shoppingList: [] }),

      // Market Selection
      selectedMarketIds: [],
      toggleMarketSelection: (marketId) =>
        set((state) => ({
          selectedMarketIds: state.selectedMarketIds.includes(marketId)
            ? state.selectedMarketIds.filter(id => id !== marketId)
            : [...state.selectedMarketIds, marketId]
        })),
      clearMarketSelection: () => set({ selectedMarketIds: [] }),

      // Search
      searchResults: [],
      setSearchResults: (results) => set({ searchResults: results }),
      clearSearchResults: () => set({ searchResults: [] }),
      
      // Search loading
      isSearching: false,
      setIsSearching: (loading) => set({ isSearching: loading }),

      // NFCe Processing Queue
      processingQueue: [],
      addToProcessingQueue: (item) => 
        set((state) => ({ 
          processingQueue: [item, ...state.processingQueue.filter(i => i.url !== item.url)] 
        })),
      updateProcessingItem: (recordId, updates) =>
        set((state) => ({
          processingQueue: state.processingQueue.map(item =>
            item.record_id === recordId ? { ...item, ...updates } : item
          )
        })),
      removeFromProcessingQueue: (recordId) =>
        set((state) => ({
          processingQueue: state.processingQueue.filter(i => i.record_id !== recordId)
        })),
      setProcessingQueue: (items) => set({ processingQueue: items }),
    }),
    {
      name: 'app-precos-storage',
      partialize: (state) => ({ 
        shoppingList: state.shoppingList, 
        selectedMarketIds: state.selectedMarketIds,
        processingQueue: state.processingQueue
      }),
    }
  )
);
