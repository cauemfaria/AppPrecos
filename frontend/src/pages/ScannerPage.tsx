import React, { useEffect, useRef, useState, useCallback } from 'react';
import { nfceService } from '../services/api';
import { useStore } from '../store/useStore';
import type { ProcessingItem } from '../types';
import { Search, Camera, X } from 'lucide-react';

// Type declarations for the native BarcodeDetector API
interface BarcodeDetectorResult {
  rawValue: string;
  format: string;
  boundingBox: DOMRectReadOnly;
  cornerPoints: { x: number; y: number }[];
}

interface BarcodeDetectorOptions {
  formats: string[];
}

declare global {
  interface Window {
    BarcodeDetector?: {
      new(options?: BarcodeDetectorOptions): {
        detect(source: ImageBitmapSource): Promise<BarcodeDetectorResult[]>;
      };
      getSupportedFormats(): Promise<string[]>;
    };
  }
}

const ScannerPage: React.FC = () => {
  const [manualUrl, setManualUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scannerError, setScannerError] = useState<string | null>(null);
  const [scannerMode, setScannerMode] = useState<'native' | 'fallback' | null>(null);
  
  const { 
    processingQueue, 
    addToProcessingQueue, 
    updateProcessingItem, 
    removeFromProcessingQueue 
  } = useStore();
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const recentScansRef = useRef<Record<string, number>>({});

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

  const stopScanning = useCallback(() => {
    // Stop animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    // Stop camera stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    // Clear video
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    
    setIsScanning(false);
  }, []);

  const startNativeScanner = useCallback(async () => {
    if (!window.BarcodeDetector) {
      return false;
    }

    try {
      // Check if QR code format is supported
      const formats = await window.BarcodeDetector.getSupportedFormats();
      if (!formats.includes('qr_code')) {
        console.log("QR code not supported by native detector");
        return false;
      }

      const detector = new window.BarcodeDetector({ formats: ['qr_code'] });
      
      // Get camera stream with high resolution for better QR detection
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false
      });

      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setScannerMode('native');
      
      // Detection loop
      const detectFrame = async () => {
        if (!videoRef.current || !streamRef.current) return;
        
        try {
          const barcodes = await detector.detect(videoRef.current);
          
          if (barcodes.length > 0) {
            const qrCode = barcodes[0];
            console.log("Native QR detected:", qrCode.rawValue);
            
            // Vibrate on success
            if (navigator.vibrate) navigator.vibrate(100);
            
            stopScanning();
            handleUrlSubmitted(qrCode.rawValue);
            return;
          }
        } catch (err) {
          // Ignore detection errors, just continue
        }
        
        // Continue scanning
        animationFrameRef.current = requestAnimationFrame(detectFrame);
      };
      
      animationFrameRef.current = requestAnimationFrame(detectFrame);
      return true;
      
    } catch (err) {
      console.error("Native scanner failed:", err);
      return false;
    }
  }, [stopScanning, handleUrlSubmitted]);

  const startFallbackScanner = useCallback(async () => {
    try {
      // Get camera stream
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false
      });

      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setScannerMode('fallback');

      // Import jsQR dynamically for fallback
      const { default: jsQR } = await import('jsqr');
      
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      
      if (!ctx) throw new Error("Could not get canvas context");

      // Detection loop using jsQR
      const detectFrame = () => {
        if (!videoRef.current || !streamRef.current || !ctx) return;
        
        const video = videoRef.current;
        
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(imageData.data, imageData.width, imageData.height, {
            inversionAttempts: 'dontInvert',
          });
          
          if (code && code.data) {
            console.log("jsQR detected:", code.data);
            
            // Vibrate on success
            if (navigator.vibrate) navigator.vibrate(100);
            
            stopScanning();
            handleUrlSubmitted(code.data);
            return;
          }
        }
        
        // Continue scanning
        animationFrameRef.current = requestAnimationFrame(detectFrame);
      };
      
      animationFrameRef.current = requestAnimationFrame(detectFrame);
      return true;
      
    } catch (err) {
      console.error("Fallback scanner failed:", err);
      return false;
    }
  }, [stopScanning, handleUrlSubmitted]);

  const startScanning = async () => {
    setScannerError(null);
    setIsScanning(true);
    
    // First, try native BarcodeDetector (iPhone/modern browsers)
    const nativeSuccess = await startNativeScanner();
    
    if (!nativeSuccess) {
      // Fall back to jsQR
      const fallbackSuccess = await startFallbackScanner();
      
      if (!fallbackSuccess) {
        setScannerError("Não foi possível acessar a câmera. Por favor, verifique as permissões.");
        setIsScanning(false);
      }
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopScanning();
    };
  }, [stopScanning]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold">Scanner de NFCe</h2>
        
        <div className="flex gap-2">
          <div className="relative flex-1 md:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input 
              type="text" 
              placeholder="Cole a URL da NFCe manualmente..."
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
            Adicionar URL
          </button>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center max-w-2xl mx-auto w-full">
        {/* Scanner View */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col items-center justify-center min-h-[400px] w-full">
          {!isScanning ? (
            <div className="flex flex-col items-center gap-6 text-center">
              <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center text-blue-600">
                <Camera className="w-10 h-10" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Pronto para Escanear</h3>
                <p className="text-gray-500 max-w-[280px]">Escaneie o QR code no seu cupom fiscal para extrair todos os produtos automaticamente.</p>
              </div>
              <button 
                onClick={startScanning}
                className="bg-blue-600 text-white px-8 py-3 rounded-2xl font-bold shadow-lg shadow-blue-200 hover:bg-blue-700 active:scale-95 transition-all flex items-center gap-2"
              >
                <Camera className="w-5 h-5" />
                Abrir Câmera
              </button>
              {scannerError && (
                <p className="text-red-500 text-sm bg-red-50 px-4 py-2 rounded-lg">{scannerError}</p>
              )}
            </div>
          ) : (
            <div className="w-full flex flex-col items-center gap-4 relative">
              <div className="relative w-full max-w-[400px] aspect-square rounded-2xl overflow-hidden bg-black">
                <video 
                  ref={videoRef}
                  className="absolute inset-0 w-full h-full object-cover"
                  playsInline
                  muted
                  autoPlay
                />
                {/* Scan overlay */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-3/4 h-3/4 border-2 border-white/50 rounded-2xl relative">
                    <div className="absolute top-0 left-0 w-6 h-6 border-t-4 border-l-4 border-blue-500 rounded-tl-lg" />
                    <div className="absolute top-0 right-0 w-6 h-6 border-t-4 border-r-4 border-blue-500 rounded-tr-lg" />
                    <div className="absolute bottom-0 left-0 w-6 h-6 border-b-4 border-l-4 border-blue-500 rounded-bl-lg" />
                    <div className="absolute bottom-0 right-0 w-6 h-6 border-b-4 border-r-4 border-blue-500 rounded-br-lg" />
                    {/* Scanning line animation */}
                    <div className="absolute left-2 right-2 h-0.5 bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse" 
                         style={{ top: '50%', animation: 'scan 2s ease-in-out infinite' }} />
                  </div>
                </div>
                {/* Close button */}
                <button 
                  onClick={stopScanning}
                  className="absolute top-3 right-3 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
                {/* Mode indicator */}
                {scannerMode && (
                  <div className="absolute bottom-3 left-3 bg-black/50 text-white text-xs px-2 py-1 rounded-full">
                    {scannerMode === 'native' ? '📱 Nativo' : '🔍 Padrão'}
                  </div>
                )}
              </div>
              <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                Aponte a câmera para o QR code
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* CSS for scan animation */}
      <style>{`
        @keyframes scan {
          0%, 100% { top: 20%; opacity: 0.3; }
          50% { top: 80%; opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default ScannerPage;
