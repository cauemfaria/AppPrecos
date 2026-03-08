import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { nfceService } from '../services/api';
import { useStore } from '../store/useStore';
import type { ProcessingItem } from '../types';
import { X, Link } from 'lucide-react';

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

const QRScannerPage: React.FC = () => {
  const navigate = useNavigate();
  const [isScanning, setIsScanning] = useState(false);
  const [scannerError, setScannerError] = useState<string | null>(null);
  const [scanFlash, setScanFlash] = useState(false);
  const [scanCount, setScanCount] = useState(0);
  const [showManualInput, setShowManualInput] = useState(false);
  const [manualUrl, setManualUrl] = useState('');

  const { addToProcessingQueue, updateProcessingItem, removeFromProcessingQueue } = useStore();

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const recentScansRef = useRef<Record<string, number>>({});
  const pendingUrlsRef = useRef<string[]>([]);
  const activeSubmissionsRef = useRef(0);

  const submitUrl = useCallback(async (url: string) => {
    const existing = useStore.getState().processingQueue.find(i => i.url === url);
    const tempId = existing?.record_id ?? (-Date.now() - Math.random());

    if (existing) {
      updateProcessingItem(tempId, { status: 'sending' });
    }

    try {
      const response = await nfceService.extractNFCe({ url, save: true, async: true });
      updateProcessingItem(tempId, {
        record_id: response.record_id!,
        status: 'queued',
      });
    } catch (error: any) {
      const status = error.response?.status === 409 ? 'duplicate' : 'error';
      const errorMessage = error.response?.data?.error || error.message;
      updateProcessingItem(tempId, {
        status: status as any,
        error_message: errorMessage,
      });
      setTimeout(() => {
        removeFromProcessingQueue(tempId);
      }, 5000);
    }
  }, [updateProcessingItem, removeFromProcessingQueue]);

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
    if (recentScansRef.current[url] && now - recentScansRef.current[url] < DEBOUNCE_MS) return;

    const currentQueue = useStore.getState().processingQueue;
    if (currentQueue.some(item => item.url === url)) return;

    recentScansRef.current[url] = now;

    const pendingItem: ProcessingItem = {
      record_id: -now - Math.random(),
      url,
      status: 'pending',
      addedAt: now,
      processed_at: new Date().toISOString(),
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
  }, [addToProcessingQueue, submitUrl, drainPendingQueue]);

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

  const onQrDetected = useCallback((rawValue: string) => {
    const now = Date.now();
    if (recentScansRef.current[rawValue] && now - recentScansRef.current[rawValue] < DEBOUNCE_MS) return;

    if (navigator.vibrate) navigator.vibrate(100);

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
        audio: false,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      const detectFrame = async () => {
        if (!videoRef.current || !streamRef.current) return;
        try {
          const barcodes = await detector.detect(videoRef.current);
          if (barcodes.length > 0) onQrDetected(barcodes[0].rawValue);
        } catch { /* ignore */ }
        animationFrameRef.current = requestAnimationFrame(detectFrame);
      };

      animationFrameRef.current = requestAnimationFrame(detectFrame);
      return true;
    } catch {
      return false;
    }
  }, [onQrDetected]);

  const startFallbackScanner = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      const { default: jsQR } = await import('jsqr');
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      if (!ctx) throw new Error('No canvas context');

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
          if (code?.data) onQrDetected(code.data);
        }
        animationFrameRef.current = requestAnimationFrame(detectFrame);
      };

      animationFrameRef.current = requestAnimationFrame(detectFrame);
      return true;
    } catch {
      return false;
    }
  }, [onQrDetected]);

  const startScanning = async () => {
    setScannerError(null);
    setIsScanning(true);
    setScanCount(0);
    const native = await startNativeScanner();
    if (!native) {
      const fallback = await startFallbackScanner();
      if (!fallback) {
        setScannerError('Não foi possível acessar a câmera. Verifique as permissões.');
        setIsScanning(false);
      }
    }
  };

  useEffect(() => {
    startScanning();
    return () => { stopScanning(); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleClose = () => {
    stopScanning();
    navigate('/');
  };

  const handleManualSubmit = () => {
    if (manualUrl.trim()) {
      handleUrlSubmitted(manualUrl.trim());
      setManualUrl('');
      setShowManualInput(false);
      navigate('/');
    }
  };

  return (
    <div
      className="fixed inset-0 flex flex-col"
      style={{ backgroundColor: '#000', fontFamily: 'var(--font-body)', zIndex: 200 }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 z-10"
        style={{ backgroundColor: 'var(--color-surface)' }}
      >
        <button
          onClick={handleClose}
          className="flex items-center justify-center w-9 h-9 rounded-full cursor-pointer transition-all duration-200 hover:opacity-80"
          style={{ backgroundColor: '#F1F5F9' }}
          aria-label="Fechar"
        >
          <X className="w-5 h-5" style={{ color: 'var(--color-text)' }} />
        </button>

        <h1
          className="text-base font-semibold"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
        >
          Escanear NFCe
        </h1>

        <div className="w-9 h-9" />
      </div>

      {/* Camera area */}
      <div className="flex-1 relative overflow-hidden">
        {isScanning ? (
          <>
            <video
              ref={videoRef}
              className="absolute inset-0 w-full h-full object-cover"
              playsInline
              muted
              autoPlay
            />

            {/* Green flash overlay on scan */}
            {scanFlash && (
              <div
                className="absolute inset-0 pointer-events-none transition-opacity duration-300"
                style={{ backgroundColor: 'rgba(34,197,94,0.25)' }}
              />
            )}

            {/* Scan count badge */}
            {scanCount > 0 && (
              <div
                className="absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-bold text-white pointer-events-none"
                style={{ backgroundColor: 'rgba(34,197,94,0.85)' }}
              >
                {scanCount} escaneado{scanCount !== 1 ? 's' : ''}
              </div>
            )}
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            {scannerError ? (
              <div className="text-center px-8">
                <p className="text-white text-sm">{scannerError}</p>
                <button
                  onClick={startScanning}
                  className="mt-4 px-6 py-2 rounded-full text-sm font-semibold cursor-pointer"
                  style={{ backgroundColor: 'var(--color-cta)', color: 'white' }}
                >
                  Tentar novamente
                </button>
              </div>
            ) : (
              <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
          </div>
        )}
      </div>

      {/* Instruction text */}
      <div
        className="px-6 py-4 text-center"
        style={{ backgroundColor: 'var(--color-surface)' }}
      >
        <p
          className="text-sm"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-body)' }}
        >
          Aponte para o código QR para escanear
        </p>
      </div>

      {/* Manual URL Input Modal */}
      {showManualInput && (
        <div
          className="absolute inset-x-0 bottom-0 p-4 rounded-t-2xl z-20"
          style={{ backgroundColor: 'var(--color-surface)' }}
        >
          <p
            className="text-sm font-semibold mb-3"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
          >
            Inserir URL manualmente
          </p>
          <input
            type="url"
            placeholder="https://www.sefaz..."
            value={manualUrl}
            onChange={e => setManualUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleManualSubmit()}
            autoFocus
            className="w-full px-4 py-3 rounded-xl text-sm mb-3"
            style={{
              border: '1px solid var(--color-border)',
              fontFamily: 'var(--font-body)',
              color: 'var(--color-text)',
              outline: 'none',
            }}
          />
          <div className="flex gap-2">
            <button
              onClick={() => setShowManualInput(false)}
              className="flex-1 py-3 rounded-xl text-sm font-semibold cursor-pointer transition-all duration-200"
              style={{
                backgroundColor: '#F1F5F9',
                color: 'var(--color-text-muted)',
                fontFamily: 'var(--font-body)',
              }}
            >
              Cancelar
            </button>
            <button
              onClick={handleManualSubmit}
              disabled={!manualUrl.trim()}
              className="flex-1 py-3 rounded-xl text-sm font-semibold cursor-pointer transition-all duration-200 disabled:opacity-50"
              style={{
                backgroundColor: 'var(--color-primary)',
                color: 'white',
                fontFamily: 'var(--font-body)',
              }}
            >
              Adicionar
            </button>
          </div>
        </div>
      )}

      {/* Bottom action */}
      <div
        className="px-6 pb-10 pt-2"
        style={{ backgroundColor: 'var(--color-surface)' }}
      >
        <button
          onClick={() => setShowManualInput(true)}
          className="w-full py-4 rounded-2xl text-sm font-bold flex items-center justify-center gap-2 cursor-pointer transition-all duration-200 active:scale-[0.98]"
          style={{
            backgroundColor: 'var(--color-cta)',
            color: 'white',
            fontFamily: 'var(--font-body)',
            boxShadow: '0 4px 14px rgba(249,115,22,0.3)',
          }}
        >
          <Link className="w-4 h-4" />
          Inserir URL manualmente
        </button>
      </div>

    </div>
  );
};

export default QRScannerPage;
