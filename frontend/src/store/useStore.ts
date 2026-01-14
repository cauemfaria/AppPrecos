import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ProductSearchItem, Market } from '../types';

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
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Shopping List
      shoppingList: [],
      addToShoppingList: (product) => 
        set((state) => ({
          shoppingList: state.shoppingList.some(p => p.ean === product.ean && p.product_name === product.product_name)
            ? state.shoppingList
            : [...state.shoppingList, product]
        })),
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
    }),
    {
      name: 'app-precos-storage',
      partialize: (state) => ({ 
        shoppingList: state.shoppingList, 
        selectedMarketIds: state.selectedMarketIds 
      }),
    }
  )
);
