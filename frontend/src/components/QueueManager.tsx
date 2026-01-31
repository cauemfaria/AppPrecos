import React, { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { nfceService } from '../services/api';
import type { ProcessingItem } from '../types';

const QueueManager: React.FC = () => {
  const { 
    processingQueue, 
    updateProcessingItem, 
    removeFromProcessingQueue,
    setProcessingQueue 
  } = useStore();
  
  // Initial fetch of processing items from backend
  useEffect(() => {
    const fetchInitialProcessing = async () => {
      try {
        const backendItems = await nfceService.getProcessingNfces();
        
        // Merge backend items into current queue
        // Backend items are more authoritative for status
        const now = Date.now();
        const mergedItems: ProcessingItem[] = [...processingQueue];
        
        backendItems.forEach(bItem => {
          const index = mergedItems.findIndex(i => i.record_id === bItem.record_id);
          if (index !== -1) {
            mergedItems[index] = {
              ...mergedItems[index],
              ...bItem,
              status: bItem.status as any
            };
          } else {
            mergedItems.push({
              ...bItem,
              url: bItem.nfce_url || '',
              status: bItem.status as any,
              addedAt: now
            });
          }
        });
        
        setProcessingQueue(mergedItems);
      } catch (error) {
        console.error("Failed to fetch initial processing items", error);
      }
    };

    fetchInitialProcessing();
  }, []);

  // Polling logic
  useEffect(() => {
    const pendingItems = processingQueue.filter(item => 
      item.status === 'processing' || item.status === 'extracting' || item.status === 'sending'
    );

    if (pendingItems.length === 0) return;

    const pollInterval = setInterval(async () => {
      // Refresh pending items from current store state to get latest record_ids
      const currentPending = useStore.getState().processingQueue.filter(item => 
        item.status === 'processing' || item.status === 'extracting'
      );

      for (const item of currentPending) {
        if (item.record_id < 0) continue; // Still in 'sending' state (temp ID)
        
        try {
          const status = await nfceService.getNfceStatus(item.record_id);
          
          if (status.status !== item.status) {
            updateProcessingItem(item.record_id, { 
              ...status, 
              status: status.status as any 
            });

            // If success or error, schedule removal after 5 seconds
            if (status.status === 'success' || status.status === 'error') {
              setTimeout(() => {
                removeFromProcessingQueue(item.record_id);
              }, 5000);
            }
          }
        } catch (error) {
          console.error(`Failed to poll status for ${item.record_id}`, error);
        }
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [processingQueue.length, updateProcessingItem, removeFromProcessingQueue]);

  return null; // This component doesn't render anything
};

export default QueueManager;
