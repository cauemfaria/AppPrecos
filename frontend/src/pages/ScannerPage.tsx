import React, { useEffect, useRef, useState, useCallback } from 'react';
import { nfceService } from '../services/api';
import { useStore } from '../store/useStore';
import type { ProcessingItem } from '../types';
import { Loader2, CheckCircle2, XCircle, Clock, Search, ExternalLink, AlertCircle, Camera, X } from 'lucide-react';

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

const MAX_CONCURRENT_SUBMISSIONS = 3;
const DEBOUNCE_MS = 3000;

const ScannerPage: React.FC = () => {
  const [manualUrl, setManualUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scannerError, setScannerError] = useState<string | null>(null);
  const [scannerMode, setScannerMode] = useState<'native' | 'fallback' | null>(null);
  const [scanFlash, setScanFlash] = useState(false);
  const [scanCount, setScanCount] = useState(0);

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

  // Submission throttle: local queue of URLs waiting to be sent
  const pendingUrlsRef = useRef<string[]>([]);
  const activeSubmissionsRef = useRef(0);

  const submitUrl = useCallback(async (url: string) => {
    // Find the existing pending/sending item for this URL
    const existing = useStore.getState().processingQueue.find(i => i.url === url);
    const tempId = existing?.record_id ?? (-Date.now() - Math.random());

    if (existing) {
      updateProcessingItem(tempId, { status: 'sending' });
    }

    try {
      const response = await nfceService.extractNFCe({ url, save: true, async: true });
      updateProcessingItem(tempId, {
        record_id: response.record_id!,
        status: 'queued'
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
  }, [manualUrl, updateProcessingItem, removeFromProcessingQueue]);

  const drainPendingQueue = useCallback(() => {
    while (pendingUrlsRef.current.length > 0 && activeSubmissionsRef.current < MAX_CONCURRENT_SUBMISSIONS) {
      const url = pendingUrlsRef.current.shift()!;
      activeSubmissionsRef.current++;
      submitUrl(url).finally(() => {
        activeSubmissionsRef.current--;
        drainPendingQueue();
      });
    }
  }, [submitUrl]);

  const handleUrlSubmitted = useCallback((url: string) => {
    if (!url.trim()) return;

    const now = Date.now();

    if (recentScansRef.current[url] && now - recentScansRef.current[url] < DEBOUNCE_MS) {
      return;
    }

    // Check against store directly for most up-to-date state
    const currentQueue = useStore.getState().processingQueue;
    if (currentQueue.some(item => item.url === url)) {
      return;
    }

    recentScansRef.current[url] = now;

    // Add a "pending" placeholder so it appears in the queue immediately
    const pendingItem: ProcessingItem = {
      record_id: -now - Math.random(),
      url,
      status: 'pending',
      addedAt: now,
      processed_at: new Date().toISOString()
    };
    addToProcessingQueue(pendingItem);

    if (activeSubmissionsRef.current < MAX_CONCURRENT_SUBMISSIONS) {
      activeSubmissionsRef.current++;
      submitUrl(url).finally(() => {
        activeSubmissionsRef.current--;
        drainPendingQueue();
      });
    } else {
      pendingUrlsRef.current.push(url);
    }
  }, [addToProcessingQueue, updateProcessingItem, submitUrl, drainPendingQueue]);

  const stopScanning = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsScanning(false);
    setScanCount(0);
  }, []);

  // Continuous scanning: submit URL without stopping the camera
  const onQrDetected = useCallback((rawValue: string) => {
    const now = Date.now();
    if (recentScansRef.current[rawValue] && now - recentScansRef.current[rawValue] < DEBOUNCE_MS) {
      return;
    }

    if (navigator.vibrate) navigator.vibrate(100);

    // Green flash feedback
    setScanFlash(true);
    setTimeout(() => setScanFlash(false), 400);
    setScanCount(prev => prev + 1);

    handleUrlSubmitted(rawValue);
  }, [handleUrlSubmitted]);

  const startNativeScanner = useCallback(async () => {
    if (!window.BarcodeDetector) return false;

    try {
      const formats = await window.BarcodeDetector.getSupportedFormats();
      if (!formats.includes('qr_code')) return false;

      const detector = new window.BarcodeDetector({ formats: ['qr_code'] });

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setScannerMode('native');

      const detectFrame = async () => {
        if (!videoRef.current || !streamRef.current) return;

        try {
          const barcodes = await detector.detect(videoRef.current);
          if (barcodes.length > 0) {
            onQrDetected(barcodes[0].rawValue);
          }
        } catch {
          // Ignore detection errors
        }

        animationFrameRef.current = requestAnimationFrame(detectFrame);
      };

      animationFrameRef.current = requestAnimationFrame(detectFrame);
      return true;
    } catch (err) {
      console.error("Native scanner failed:", err);
      return false;
    }
  }, [onQrDetected]);

  const startFallbackScanner = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setScannerMode('fallback');

      const { default: jsQR } = await import('jsqr');
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      if (!ctx) throw new Error("Could not get canvas context");

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
            onQrDetected(code.data);
          }
        }

        animationFrameRef.current = requestAnimationFrame(detectFrame);
      };

      animationFrameRef.current = requestAnimationFrame(detectFrame);
      return true;
    } catch (err) {
      console.error("Fallback scanner failed:", err);
      return false;
    }
  }, [onQrDetected]);

  const startScanning = async () => {
    setScannerError(null);
    setIsScanning(true);
    setScanCount(0);

    const nativeSuccess = await startNativeScanner();
    if (!nativeSuccess) {
      const fallbackSuccess = await startFallbackScanner();
      if (!fallbackSuccess) {
        setScannerError("Nao foi possivel acessar a camera. Por favor, verifique as permissoes.");
        setIsScanning(false);
      }
    }
  };

  useEffect(() => {
    return () => { stopScanning(); };
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scanner View */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col items-center justify-center min-h-[400px]">
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
                Abrir Camera
              </button>
              {scannerError && (
                <p className="text-red-500 text-sm bg-red-50 px-4 py-2 rounded-lg">{scannerError}</p>
              )}
            </div>
          ) : (
            <div className="w-full flex flex-col items-center gap-4 relative">
              <div className={`relative w-full max-w-[400px] aspect-square rounded-2xl overflow-hidden bg-black transition-all duration-300 ${scanFlash ? 'ring-4 ring-green-400' : ''}`}>
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
                    <div className="absolute left-2 right-2 h-0.5 bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-pulse"
                         style={{ top: '50%', animation: 'scan 2s ease-in-out infinite' }} />
                  </div>
                </div>
                {/* Green flash overlay */}
                {scanFlash && (
                  <div className="absolute inset-0 bg-green-400/20 pointer-events-none transition-opacity duration-300" />
                )}
                {/* Close button */}
                <button
                  onClick={stopScanning}
                  className="absolute top-3 right-3 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
                {/* Mode + scan count indicator */}
                <div className="absolute bottom-3 left-3 flex items-center gap-2">
                  {scannerMode && (
                    <div className="bg-black/50 text-white text-xs px-2 py-1 rounded-full">
                      {scannerMode === 'native' ? 'Nativo' : 'Padrao'}
                    </div>
                  )}
                  {scanCount > 0 && (
                    <div className="bg-green-500 text-white text-xs px-2 py-1 rounded-full font-bold">
                      {scanCount} escaneado{scanCount !== 1 ? 's' : ''}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                Escaneie varios QR codes seguidos
              </div>
            </div>
          )}
        </div>

        {/* Processing Queue */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[500px]">
          <h3 className="text-lg font-bold mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-600" />
              Fila de Processamento
            </div>
            {processingQueue.length > 0 && (
              <span className="bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded-full">
                {processingQueue.length} itens
              </span>
            )}
          </h3>

          <div className="flex-1 overflow-auto pr-2 space-y-3">
            {processingQueue.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 p-8">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                  <Clock className="w-8 h-8 opacity-20" />
                </div>
                <p className="font-medium text-gray-500">Nenhum processo ativo</p>
                <p className="text-sm max-w-[200px] mt-1">Cupons escaneados aparecerao aqui durante o processamento.</p>
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
                            item.status === 'pending' ? 'Aguardando envio...' :
                            item.status === 'sending' ? 'Enviando ao servidor...' :
                            item.status === 'queued' ? 'Na fila do servidor...' :
                            item.status === 'duplicate' ? 'Ja existe no sistema' :
                            'Processando mercado...'
                          )}
                        </p>
                      </div>

                      {item.status === 'error' ? (
                        <p className="text-xs text-red-500 line-clamp-2">{item.error_message}</p>
                      ) : item.status === 'duplicate' ? (
                        <p className="text-xs text-orange-500">Este cupom ja foi adicionado.</p>
                      ) : (
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          {item.products_count ? (
                            <span className="font-medium text-blue-600">{item.products_count} produtos</span>
                          ) : (
                            <span className="flex items-center gap-1 italic">
                              {item.status === 'extracting' ? 'Extraindo itens...' :
                               item.status === 'queued' ? 'Aguardando vez...' :
                               item.status === 'pending' ? 'Na fila local...' :
                               'Conectando...'}
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
                      ) : item.status === 'pending' ? (
                        <Clock className="w-6 h-6 text-gray-400" />
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
                        Ver mercado <ExternalLink className="w-3 h-3" />
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
                Itens sao removidos automaticamente apos 5s
              </p>
            </div>
          )}
        </div>
      </div>

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
