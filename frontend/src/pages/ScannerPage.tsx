import React, { useEffect, useRef, useState } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { nfceService } from '../services/api';
import { NFCeStatusResponse } from '../types';
import { Loader2, CheckCircle2, XCircle, Clock, ExternalLink } from 'lucide-react';

const ScannerPage: React.FC = () => {
  const [manualUrl, setManualUrl] = useState('');
  const [processingQueue, setProcessingQueue] = useState<NFCeStatusResponse[]>([]);
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);

  useEffect(() => {
    scannerRef.current = new Html5QrcodeScanner(
      "reader",
      { fps: 10, qrbox: { width: 250, height: 250 } },
      /* verbose= */ false
    );

    scannerRef.current.render(
      (decodedText) => {
        handleUrlSubmitted(decodedText);
      },
      (error) => {
        // Handle error silently or log if needed
      }
    );

    return () => {
      if (scannerRef.current) {
        scannerRef.current.clear().catch(err => console.error("Failed to clear scanner", err));
      }
    };
  }, []);

  const handleUrlSubmitted = async (url: string) => {
    if (!url.trim()) return;
    
    try {
      const response = await nfceService.extractNFCe({ url, save: true, async: true });
      if (response.record_id) {
        // Initial status
        const initialStatus: NFCeStatusResponse = {
          record_id: response.record_id,
          status: 'processing',
          nfce_url: url, // Assuming we add this for UI
          processed_at: new Date().toISOString()
        } as any;
        
        setProcessingQueue(prev => [initialStatus, ...prev]);
        setManualUrl('');
      }
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.error || error.message}`);
    }
  };

  // Polling for processing items
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      const pendingItems = processingQueue.filter(item => 
        item.status === 'processing' || item.status === 'extracting'
      );

      if (pendingItems.length === 0) return;

      const updatedQueue = [...processingQueue];
      
      for (const item of pendingItems) {
        try {
          const status = await nfceService.getNfceStatus(item.record_id);
          const index = updatedQueue.findIndex(i => i.record_id === item.record_id);
          if (index !== -1) {
            updatedQueue[index] = status;
          }
        } catch (error) {
          console.error("Failed to poll status", error);
        }
      }

      setProcessingQueue(updatedQueue);
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [processingQueue]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold">NFCe Scanner</h2>
        
        <div className="flex gap-2">
          <input 
            type="text" 
            placeholder="Paste NFCe URL manually..."
            className="flex-1 md:w-64 px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            value={manualUrl}
            onChange={(e) => setManualUrl(e.target.value)}
          />
          <button 
            onClick={() => handleUrlSubmitted(manualUrl)}
            className="bg-blue-600 text-white px-6 py-2 rounded-xl font-medium hover:bg-blue-700 transition-colors"
          >
            Submit
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scanner View */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <div id="reader" className="overflow-hidden rounded-2xl border-0"></div>
          <p className="mt-4 text-center text-sm text-gray-500">
            Point your camera at the QR code on the receipt
          </p>
        </div>

        {/* Processing Queue */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            Recent Scans
          </h3>
          
          <div className="space-y-4 max-h-[400px] overflow-auto pr-2">
            {processingQueue.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <p>No recent scans to show.</p>
              </div>
            ) : (
              processingQueue.map((item) => (
                <div key={item.record_id} className="p-4 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold truncate">
                      {item.market_name || 'Processing Market...'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {item.products_count ? `${item.products_count} products` : 'Extracting data...'}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {item.status === 'success' ? (
                      <CheckCircle2 className="w-6 h-6 text-green-500" />
                    ) : item.status === 'error' ? (
                      <XCircle className="w-6 h-6 text-red-500" />
                    ) : (
                      <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScannerPage;
