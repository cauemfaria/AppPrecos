import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/useStore';
import { scanService } from '../services/api';
import { X, CheckCircle2, AlertTriangle } from 'lucide-react';
import { BarcodeDetector as BarcodeDetectorPolyfill } from 'barcode-detector/pure';

type BarcodeDetectorLike = {
  detect: (source: CanvasImageSource) => Promise<Array<{ rawValue: string }>>;
};

type BarcodeDetectorCtor = new (opts: { formats: string[] }) => BarcodeDetectorLike;

const sanitizePriceInput = (raw: string) => {
  // Allow only digits and a single separator (comma or dot)
  let cleaned = raw.replace(/[^\d.,]/g, '');
  // Normalise: keep only the first separator
  const firstSep = cleaned.search(/[.,]/);
  if (firstSep !== -1) {
    const head = cleaned.slice(0, firstSep + 1);
    const tail = cleaned.slice(firstSep + 1).replace(/[.,]/g, '');
    cleaned = head + tail;
  }
  return cleaned;
};

const parsePrice = (raw: string): number | null => {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const n = parseFloat(trimmed.replace(',', '.'));
  return Number.isFinite(n) ? n : null;
};

const BarcodeScannerPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedMarket, incrementScanCount, addScan, scanCount } = useStore();

  const [isScanning, setIsScanning] = useState(false);
  const [scannerError, setScannerError] = useState<string | null>(null);
  const [scanFlash, setScanFlash] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [detectedEan, setDetectedEan] = useState('');

  // Price entry state
  const [varejoInput, setVarejoInput] = useState('');
  const [atacadoInput, setAtacadoInput] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const isPausedRef = useRef(false);
  const detectFrameRef = useRef<(() => void) | null>(null);
  const varejoInputRef = useRef<HTMLInputElement>(null);

  const pauseDetection = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    isPausedRef.current = true;
    setIsPaused(true);
  }, []);

  const resumeDetection = useCallback(() => {
    if (!detectFrameRef.current) return;
    isPausedRef.current = false;
    setIsPaused(false);
    setDetectedEan('');
    setVarejoInput('');
    setAtacadoInput('');
    setSaveError(null);
    animationFrameRef.current = requestAnimationFrame(detectFrameRef.current);
  }, []);

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
    isPausedRef.current = false;
    detectFrameRef.current = null;
    setIsScanning(false);
    setIsPaused(false);
  }, []);

  const onBarcodeDetected = useCallback((rawValue: string) => {
    pauseDetection();
    if (navigator.vibrate) navigator.vibrate(100);
    setDetectedEan(rawValue);
    setTimeout(() => varejoInputRef.current?.focus(), 200);
  }, [pauseDetection]);

  const startScanner = useCallback(async () => {
    const targetFormats = ['ean_13', 'ean_8', 'upc_a'];

    // Use native BarcodeDetector if available (Chrome/Android), otherwise polyfill (Safari/iOS)
    const nativeDetector = (window as unknown as { BarcodeDetector?: BarcodeDetectorCtor & {
      getSupportedFormats?: () => Promise<string[]>;
    } }).BarcodeDetector;
    const DetectorClass: BarcodeDetectorCtor & { getSupportedFormats?: () => Promise<string[]> } =
      nativeDetector ?? (BarcodeDetectorPolyfill as unknown as BarcodeDetectorCtor & {
        getSupportedFormats?: () => Promise<string[]>;
      });

    try {
      if (DetectorClass.getSupportedFormats) {
        const supported = await DetectorClass.getSupportedFormats();
        const available = targetFormats.filter(f => supported.includes(f));
        if (available.length === 0) throw new Error('No EAN formats supported');
      }

      const detector = new DetectorClass({ formats: targetFormats });
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
        if (!videoRef.current || !streamRef.current || isPausedRef.current) return;
        try {
          const barcodes = await detector.detect(videoRef.current);
          if (barcodes.length > 0) {
            onBarcodeDetected(barcodes[0].rawValue);
            return;
          }
        } catch { /* ignore frame errors */ }
        if (!isPausedRef.current) {
          animationFrameRef.current = requestAnimationFrame(detectFrame);
        }
      };

      detectFrameRef.current = detectFrame;
      animationFrameRef.current = requestAnimationFrame(detectFrame);
      return true;
    } catch (err) {
      console.error('Scanner init failed', err);
      return false;
    }
  }, [onBarcodeDetected]);

  const startScanning = useCallback(async () => {
    setScannerError(null);
    setIsScanning(true);
    isPausedRef.current = false;
    const ok = await startScanner();
    if (!ok) {
      setScannerError('Não foi possível acessar a câmera. Verifique as permissões do navegador.');
      setIsScanning(false);
    }
  }, [startScanner]);

  useEffect(() => {
    if (selectedMarket) startScanning();
    return () => { stopScanning(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSave = async () => {
    if (!selectedMarket || !detectedEan || isSaving) return;
    const varejo = parsePrice(varejoInput);
    if (varejo === null || varejo <= 0) {
      setSaveError('Informe um preço varejo válido');
      varejoInputRef.current?.focus();
      return;
    }

    const atacadoRaw = atacadoInput.trim();
    let atacado: number | undefined;
    if (atacadoRaw) {
      const parsed = parsePrice(atacadoRaw);
      if (parsed === null || parsed <= 0) {
        setSaveError('Preço atacado inválido');
        return;
      }
      atacado = parsed;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      await scanService.saveScan({
        market_id: selectedMarket.market_id,
        ean: detectedEan,
        varejo_price: varejo,
        atacado_price: atacado,
      });

      incrementScanCount();
      addScan({
        ean: detectedEan,
        varejo_price: varejo,
        atacado_price: atacado,
        savedAt: Date.now(),
      });

      setScanFlash(true);
      setTimeout(() => setScanFlash(false), 400);

      setTimeout(() => resumeDetection(), 500);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } }; isBackendDown?: boolean; message?: string };
      const message = e.isBackendDown
        ? 'Servidor inacessível. Verifique sua conexão.'
        : e.response?.data?.error || e.message || 'Falha ao salvar';
      setSaveError(message);
    } finally {
      setIsSaving(false);
    }
  };

  // No market selected
  if (!selectedMarket) {
    return (
      <div
        className="p-4 flex flex-col items-center justify-center min-h-[70vh] text-center"
        style={{ fontFamily: 'var(--font-body)' }}
      >
        <div
          className="w-16 h-16 flex items-center justify-center rounded-2xl mb-4"
          style={{ backgroundColor: 'color-mix(in srgb, var(--color-cta) 8%, var(--color-surface))' }}
        >
          <AlertTriangle className="w-8 h-8" style={{ color: 'var(--color-cta)' }} />
        </div>
        <h2
          className="text-lg font-bold mb-2"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
        >
          Nenhum mercado selecionado
        </h2>
        <p className="text-sm mb-6" style={{ color: 'var(--color-text-muted)' }}>
          Selecione um mercado na tela inicial antes de escanear.
        </p>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="px-6 py-3 rounded-xl text-sm font-semibold cursor-pointer transition-all duration-200 active:scale-[0.97]"
          style={{
            backgroundColor: 'var(--color-primary)',
            color: 'white',
            fontFamily: 'var(--font-body)',
          }}
        >
          Ir para Início
        </button>
      </div>
    );
  }

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
          type="button"
          onClick={() => { stopScanning(); navigate('/'); }}
          className="flex items-center justify-center w-9 h-9 rounded-full cursor-pointer transition-all duration-200 hover:opacity-80"
          style={{ backgroundColor: 'var(--color-bg-subtle)' }}
          aria-label="Fechar"
        >
          <X className="w-5 h-5" style={{ color: 'var(--color-text)' }} />
        </button>

        <div className="text-center min-w-0 px-2">
          <h1
            className="text-base font-semibold truncate"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
          >
            Escanear Código
          </h1>
          <p className="text-xs truncate" style={{ color: 'var(--color-text-muted)' }}>
            {selectedMarket.name}
          </p>
        </div>

        {scanCount > 0 ? (
          <div
            className="flex items-center justify-center h-9 px-3 rounded-full text-xs font-bold text-white"
            style={{ backgroundColor: 'var(--color-text-info)', minWidth: '2.25rem' }}
            aria-label={`${scanCount} escaneamentos`}
          >
            {scanCount}
          </div>
        ) : (
          <div className="w-9 h-9" />
        )}
      </div>

      {/* Camera */}
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

            {scanFlash && (
              <div
                className="absolute inset-0 pointer-events-none transition-opacity duration-300"
                style={{ backgroundColor: 'rgba(34,197,94,0.25)' }}
              />
            )}

            {/* Price Entry Bottom Sheet */}
            {isPaused && detectedEan && (
              <div className="absolute inset-0 flex flex-col justify-end" style={{ backgroundColor: 'rgba(0,0,0,0.55)' }}>
                <div
                  className="rounded-t-2xl p-5 space-y-4"
                  style={{ backgroundColor: 'var(--color-surface)' }}
                >
                  {/* EAN Display */}
                  <div className="flex items-center gap-3">
                    <div
                      className="flex items-center justify-center w-10 h-10 rounded-xl shrink-0"
                      style={{ backgroundColor: 'color-mix(in srgb, var(--color-success) 8%, var(--color-surface))' }}
                    >
                      <CheckCircle2 className="w-5 h-5" style={{ color: 'var(--color-success)' }} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Código EAN</p>
                      <p
                        className="text-lg font-bold font-mono truncate"
                        style={{ color: 'var(--color-text)', fontFamily: 'var(--font-heading)' }}
                      >
                        {detectedEan}
                      </p>
                    </div>
                  </div>

                  {/* Price Inputs */}
                  <div className="space-y-3">
                    <div>
                      <label htmlFor="varejo-price" className="text-xs font-semibold mb-1 block" style={{ color: 'var(--color-text)' }}>
                        Preço Varejo *
                      </label>
                      <div className="relative">
                        <span
                          className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-semibold pointer-events-none"
                          style={{ color: 'var(--color-text-muted)' }}
                        >
                          R$
                        </span>
                        <input
                          id="varejo-price"
                          ref={varejoInputRef}
                          type="text"
                          inputMode="decimal"
                          autoComplete="off"
                          placeholder="0,00"
                          value={varejoInput}
                          onChange={e => setVarejoInput(sanitizePriceInput(e.target.value))}
                          onKeyDown={e => e.key === 'Enter' && handleSave()}
                          className="w-full pl-10 pr-4 py-3 rounded-xl text-sm font-semibold"
                          style={{
                            border: '1px solid var(--color-border)',
                            backgroundColor: 'var(--color-bg-muted)',
                            color: 'var(--color-text)',
                            fontFamily: 'var(--font-body)',
                            outline: 'none',
                          }}
                          onFocus={e => (e.target.style.borderColor = 'var(--color-cta)')}
                          onBlur={e => (e.target.style.borderColor = 'var(--color-border)')}
                        />
                      </div>
                    </div>

                    <div>
                      <label htmlFor="atacado-price" className="text-xs font-semibold mb-1 block" style={{ color: 'var(--color-text-muted)' }}>
                        Preço Atacado (opcional)
                      </label>
                      <div className="relative">
                        <span
                          className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-semibold pointer-events-none"
                          style={{ color: 'var(--color-text-muted)' }}
                        >
                          R$
                        </span>
                        <input
                          id="atacado-price"
                          type="text"
                          inputMode="decimal"
                          autoComplete="off"
                          placeholder="0,00"
                          value={atacadoInput}
                          onChange={e => setAtacadoInput(sanitizePriceInput(e.target.value))}
                          onKeyDown={e => e.key === 'Enter' && handleSave()}
                          className="w-full pl-10 pr-4 py-3 rounded-xl text-sm"
                          style={{
                            border: '1px solid var(--color-border)',
                            backgroundColor: 'var(--color-bg-muted)',
                            color: 'var(--color-text)',
                            fontFamily: 'var(--font-body)',
                            outline: 'none',
                          }}
                          onFocus={e => (e.target.style.borderColor = 'var(--color-primary)')}
                          onBlur={e => (e.target.style.borderColor = 'var(--color-border)')}
                        />
                      </div>
                    </div>
                  </div>

                  {saveError && (
                    <p
                      role="alert"
                      className="text-xs font-semibold text-center px-3 py-2 rounded-lg"
                      style={{
                        color: 'var(--color-error)',
                        backgroundColor: 'color-mix(in srgb, var(--color-error) 5%, var(--color-surface))',
                        border: '1px solid color-mix(in srgb, var(--color-error) 20%, var(--color-surface))',
                      }}
                    >
                      {saveError}
                    </p>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={resumeDetection}
                      disabled={isSaving}
                      className="flex-1 py-3.5 rounded-xl text-sm font-semibold cursor-pointer transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{
                        backgroundColor: 'var(--color-bg-subtle)',
                        color: 'var(--color-text-muted)',
                        fontFamily: 'var(--font-body)',
                      }}
                    >
                      Pular
                    </button>
                    <button
                      type="button"
                      onClick={handleSave}
                      disabled={isSaving || !varejoInput.trim()}
                      className="flex-[2] py-3.5 rounded-xl text-sm font-bold flex items-center justify-center gap-2 cursor-pointer transition-all duration-200 active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{
                        backgroundColor: 'var(--color-cta)',
                        color: 'white',
                        fontFamily: 'var(--font-body)',
                        boxShadow: '0 4px 14px rgba(249,115,22,0.3)',
                      }}
                    >
                      {isSaving ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <>
                          <CheckCircle2 className="w-4 h-4" />
                          Salvar
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            {scannerError ? (
              <div className="text-center px-8 max-w-sm">
                <div
                  className="w-14 h-14 mx-auto flex items-center justify-center rounded-2xl mb-3"
                  style={{ backgroundColor: 'rgba(239,68,68,0.15)' }}
                >
                  <AlertTriangle className="w-7 h-7" style={{ color: 'var(--color-error)' }} />
                </div>
                <p className="text-white text-sm font-medium">{scannerError}</p>
                <button
                  type="button"
                  onClick={startScanning}
                  className="mt-4 px-6 py-2 rounded-full text-sm font-semibold cursor-pointer transition-all duration-200 active:scale-[0.97]"
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

      {/* Bottom instruction */}
      {!isPaused && isScanning && (
        <div
          className="px-6 py-4 text-center"
          style={{ backgroundColor: 'var(--color-surface)' }}
        >
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Aponte para o código de barras do produto
          </p>
        </div>
      )}
    </div>
  );
};

export default BarcodeScannerPage;
