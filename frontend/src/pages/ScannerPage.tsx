import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { nfceService } from '../services/api';
import { useStore } from '../store/useStore';
import type { ProcessingItem } from '../types';
import { Loader2, CheckCircle2, XCircle, Clock, Search, ExternalLink, AlertCircle, Camera } from 'lucide-react';

const ScannerPage: React.FC = () => {
  const [manualUrl, setManualUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scannerError, setScannerError] = useState<string | null>(null);
  
  const { 
    processingQueue, 
    addToProcessingQueue, 
    updateProcessingItem, 
    removeFromProcessingQueue 
  } = useStore();
  
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const recentScansRef = useRef<Record<string, number>>({});

  const stopScanning = useCallback(async () => {
    if (scannerRef.current && scannerRef.current.isScanning) {
      try {
        await scannerRef.current.stop();
        setIsScanning(false);
      } catch (err) {
        console.error("Failed to stop scanner", err);
      }
    }
  }, []);

  const handleUrlSubmitted = useCallback(async (url: string) => {
    if (!url.trim()) return;
    
    const now = Date.now();
    const DEBOUNCE_MS = 3000;
    
    if (recentScansRef.current[url] && now - recentScansRef.current[url] < DEBOUNCE_MS) {
      return;
    }
    
    if (processingQueue.some(item => item.url === url)) {
      return;
    }

    recentScansRef.current[url] = now;
    const tempId = -Date.now() - Math.random();
    
    const newItem: ProcessingItem = {
      record_id: tempId,
      url,
      status: 'sending',
      addedAt: now,
      processed_at: new Date().toISOString()
    };

    addToProcessingQueue(newItem);

    try {
      const response = await nfceService.extractNFCe({ url, save: true, async: true });
      updateProcessingItem(tempId, { 
        record_id: response.record_id!, 
        status: 'processing' 
      });
      if (url === manualUrl) setManualUrl('');
    } catch (error: any) {
      const status = error.response?.status === 409 ? 'duplicate' : 'error';
      const errorMessage = error.response?.data?.error || error.message;
      updateProcessingItem(tempId, { 
        status: status as any, 
        error_message: errorMessage 
      });
      setTimeout(() => {
        removeFromProcessingQueue(tempId);
      }, 5000);
    }
  }, [manualUrl, processingQueue, addToProcessingQueue, updateProcessingItem, removeFromProcessingQueue]);

  const startScanning = async () => {
    setScannerError(null);
    setIsScanning(true);
    
    if (scannerRef.current && scannerRef.current.isScanning) {
      try {
        await scannerRef.current.stop();
      } catch (err) {
        console.error("Failed to stop previous scanner", err);
      }
    }
  };

  useEffect(() => {
    let isMounted = true;

    const initScanner = async () => {
      if (isScanning) {
        try {
          const scanner = new Html5Qrcode("reader", { 
            verbose: false,
            experimentalFeatures: {
              useBarCodeDetectorIfSupported: true 
            }
          });
          scannerRef.current = scanner;
          
          await scanner.start(
            { facingMode: "environment" },
            {
              fps: 20,
              qrbox: (viewfinderWidth, viewFinderHeight) => {
                const size = Math.min(viewfinderWidth, viewFinderHeight) * 0.8;
                return { width: size, height: size };
              },
              aspectRatio: 1.0,
              videoConstraints: {
                width: { min: 640, ideal: 1280, max: 1920 },
                height: { min: 480, ideal: 720, max: 1080 },
                facingMode: "environment"
              }
            },
            async (decodedText) => {
              if (isMounted) {
                console.log("QR Code detected:", decodedText);
                if (navigator.vibrate) navigator.vibrate(100);
                
                try {
                  await scanner.stop();
                } catch (e) {
                  console.error("Error stopping after success", e);
                }
                setIsScanning(false);
                handleUrlSubmitted(decodedText);
              }
            },
            () => {}
          );
        } catch (err: any) {
          if (isMounted) {
            console.error("Failed to start scanner", err);
            const errorMsg = err.toString().includes("Permission denied") 
              ? "Camera permission denied. Please enable it in browser settings."
              : "Failed to access camera. It might be in use by another app.";
            setScannerError(errorMsg);
            setIsScanning(false);
          }
        }
      }
    };

    if (isScanning) {
      const timer = setTimeout(initScanner, 200);
      return () => {
        clearTimeout(timer);
        isMounted = false;
      };
    }
  }, [isScanning, handleUrlSubmitted]);

  useEffect(() => {
    return () => {
      if (scannerRef.current && scannerRef.current.isScanning) {
        scannerRef.current.stop().catch(console.error);
      }
    };
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold">NFCe Scanner</h2>
        
        <div className="flex gap-2">
          <div className="relative flex-1 md:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input 
              type="text" 
              placeholder="Paste NFCe URL manually..."
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm"
              value={manualUrl}
              onChange={(e) => setManualUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleUrlSubmitted(manualUrl)}
            />
          </div>
          <button 
            onClick={() => handleUrlSubmitted(manualUrl)}
            disabled={!manualUrl.trim()}
            className="bg-blue-600 text-white px-6 py-2 rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm whitespace-nowrap"
          >
            Add URL
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scanner View */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col items-center justify-center min-h-[400px]">
          {!isScanning ? (
            <div className="flex flex-col items-center gap-6 text-center">
              <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center text-blue-600">
                <Camera className="w-10 h-10" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Ready to Scan</h3>
                <p className="text-gray-500 max-w-[280px]">Scan the QR code on your printed receipt to automatically extract all products.</p>
              </div>
              <button 
                onClick={startScanning}
                className="bg-blue-600 text-white px-8 py-3 rounded-2xl font-bold shadow-lg shadow-blue-200 hover:bg-blue-700 active:scale-95 transition-all flex items-center gap-2"
              >
                <Camera className="w-5 h-5" />
                Open Camera
              </button>
              {scannerError && (
                <p className="text-red-500 text-sm bg-red-50 px-4 py-2 rounded-lg">{scannerError}</p>
              )}
            </div>
          ) : (
            <div className="w-full flex flex-col items-center gap-4">
              <div id="reader" className="overflow-hidden rounded-2xl border-0 bg-black w-full aspect-square max-w-[400px] [&_video]:object-cover"></div>
              <button 
                onClick={stopScanning}
                className="text-gray-500 font-medium hover:text-gray-700 px-4 py-2"
              >
                Cancel
              </button>
            </div>
          )}
          
          {isScanning && (
            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              Point camera at QR code
            </div>
          )}
        </div>

        {/* Processing Queue */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[500px]">
          <h3 className="text-lg font-bold mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-600" />
              Processing Queue
            </div>
            {processingQueue.length > 0 && (
              <span className="bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded-full">
                {processingQueue.length} items
              </span>
            )}
          </h3>
          
          <div className="flex-1 overflow-auto pr-2 space-y-3">
            {processingQueue.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 p-8">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                  <Clock className="w-8 h-8 opacity-20" />
                </div>
                <p className="font-medium text-gray-500">No active processes</p>
                <p className="text-sm max-w-[200px] mt-1">Scanned receipts will appear here while processing.</p>
              </div>
            ) : (
              processingQueue.map((item) => (
                <div key={item.record_id} className={`p-4 rounded-2xl border transition-all ${
                  item.status === 'success' ? 'bg-green-50 border-green-100' :
                  item.status === 'error' ? 'bg-red-50 border-red-100' :
                  item.status === 'duplicate' ? 'bg-orange-50 border-orange-100' :
                  'bg-gray-50 border-gray-100'
                }`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className={`font-bold truncate ${
                          item.status === 'success' ? 'text-green-800' :
                          item.status === 'error' ? 'text-red-800' :
                          item.status === 'duplicate' ? 'text-orange-800' :
                          'text-gray-800'
                        }`}>
                          {item.market_name || (
                            item.status === 'sending' ? 'Sending to server...' :
                            item.status === 'duplicate' ? 'Already in system' :
                            'Processing market...'
                          )}
                        </p>
                      </div>
                      
                      {item.status === 'error' ? (
                        <p className="text-xs text-red-500 line-clamp-2">{item.error_message}</p>
                      ) : item.status === 'duplicate' ? (
                        <p className="text-xs text-orange-500">This receipt was already added.</p>
                      ) : (
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          {item.products_count ? (
                            <span className="font-medium text-blue-600">{item.products_count} products</span>
                          ) : (
                            <span className="flex items-center gap-1 italic">
                              {item.status === 'extracting' ? 'Extracting items...' : 'Connecting...'}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="shrink-0 pt-1">
                      {item.status === 'success' ? (
                        <CheckCircle2 className="w-6 h-6 text-green-500" />
                      ) : item.status === 'error' ? (
                        <XCircle className="w-6 h-6 text-red-500" />
                      ) : item.status === 'duplicate' ? (
                        <AlertCircle className="w-6 h-6 text-orange-500" />
                      ) : (
                        <div className="relative">
                          <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {item.status === 'success' && (
                    <div className="mt-3 pt-3 border-t border-green-100 flex justify-end">
                      <button className="text-[10px] font-bold text-green-700 uppercase tracking-wider flex items-center gap-1 hover:underline">
                        View market <ExternalLink className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
          
          {processingQueue.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-[10px] text-gray-400 text-center uppercase tracking-widest font-bold">
                Items are removed automatically after 5s
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScannerPage;
