import { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { nfceService } from '../services/api';
import type { ProcessingItem } from '../types';

const STALE_THRESHOLD_MS = 15 * 60 * 1000; // 15 minutes
const POLL_INTERVAL_MS = 3000;

const QueueManager: React.FC = () => {
  const {
    processingQueue,
    updateProcessingItem,
    removeFromProcessingQueue,
    setProcessingQueue
  } = useStore();

  // Stable ref so the polling interval never needs to be re-created
  const queueRef = useRef(processingQueue);
  queueRef.current = processingQueue;

  // Stale item cleanup + initial backend sync (runs once on mount)
  useEffect(() => {
    const init = async () => {
      const now = Date.now();
      const current = useStore.getState().processingQueue;

      // Remove items that are already in a terminal state (persisted from a previous session)
      // and items stuck in a non-terminal state for more than 15 minutes
      const idsToRemove = current
        .filter(item =>
          ['success', 'error', 'duplicate'].includes(item.status) ||
          (now - item.addedAt > STALE_THRESHOLD_MS &&
            !['success', 'error', 'duplicate'].includes(item.status))
        )
        .map(item => item.record_id);

      if (idsToRemove.length > 0) {
        const cleaned = current.filter(item => !idsToRemove.includes(item.record_id));
        setProcessingQueue(cleaned);
        console.log(`[QueueManager] Cleaned ${idsToRemove.length} completed/stale items on startup`);
      }

      // Merge with backend state
      try {
        const backendItems = await nfceService.getProcessingNfces();
        const merged: ProcessingItem[] = [...useStore.getState().processingQueue];

        backendItems.forEach(bItem => {
          const index = merged.findIndex(i => i.record_id === bItem.record_id);
          if (index !== -1) {
            merged[index] = { ...merged[index], ...bItem, status: bItem.status as any };
          } else {
            merged.push({
              ...bItem,
              url: bItem.nfce_url || '',
              status: bItem.status as any,
              addedAt: now
            });
          }
        });

        setProcessingQueue(merged);
      } catch (error) {
        console.error('[QueueManager] Failed to fetch initial processing items', error);
      }
    };

    init();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Single polling interval that uses a stable ref (never re-created)
  useEffect(() => {
    const poll = async () => {
      const currentQueue = queueRef.current;
      const pendingIds = currentQueue
        .filter(item =>
          ['queued', 'processing', 'extracting'].includes(item.status) &&
          item.record_id > 0
        )
        .map(item => item.record_id);

      if (pendingIds.length === 0) return;

      try {
        const statuses = await nfceService.batchGetStatus(pendingIds);

        for (const status of statuses) {
          const existing = currentQueue.find(i => i.record_id === status.record_id);
          if (!existing || existing.status === status.status) continue;

          updateProcessingItem(status.record_id, {
            ...status,
            status: status.status as any
          });

          if (status.status === 'success' || status.status === 'error') {
            setTimeout(() => {
              removeFromProcessingQueue(status.record_id);
            }, 5000);
          }
        }
      } catch (error) {
        console.error('[QueueManager] Batch poll error', error);
      }
    };

    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [updateProcessingItem, removeFromProcessingQueue]); // stable zustand functions

  return null;
};

export default QueueManager;
