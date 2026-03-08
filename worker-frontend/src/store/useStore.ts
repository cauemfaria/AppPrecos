import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Market, ScanRecord } from '../types';

interface WorkerState {
  selectedMarket: Market | null;
  setSelectedMarket: (market: Market | null) => void;

  scanCount: number;
  incrementScanCount: () => void;
  resetScanCount: () => void;

  recentScans: ScanRecord[];
  addScan: (scan: ScanRecord) => void;
  clearScans: () => void;
}

export const useStore = create<WorkerState>()(
  persist(
    (set) => ({
      selectedMarket: null,
      setSelectedMarket: (market) => set({ selectedMarket: market }),

      scanCount: 0,
      incrementScanCount: () => set((s) => ({ scanCount: s.scanCount + 1 })),
      resetScanCount: () => set({ scanCount: 0 }),

      recentScans: [],
      addScan: (scan) =>
        set((s) => ({
          recentScans: [scan, ...s.recentScans].slice(0, 50),
        })),
      clearScans: () => set({ recentScans: [], scanCount: 0 }),
    }),
    {
      name: 'worker-app-storage-v1',
      partialize: (state) => ({
        selectedMarket: state.selectedMarket,
        scanCount: state.scanCount,
        recentScans: state.recentScans,
      }),
    }
  )
);
