import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Store, ScanBarcode, ChevronDown, Barcode, MapPin, AlertCircle } from 'lucide-react';
import { useStore } from '../store/useStore';
import { marketService } from '../services/api';
import { useConnection } from '../contexts/ConnectionContext';
import type { Market } from '../types';

const HomePage: React.FC = () => {
  const { isConnected } = useConnection();
  const navigate = useNavigate();
  const { selectedMarket, setSelectedMarket, scanCount, recentScans } = useStore();
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    marketService.getMarkets()
      .then(data => { if (!cancelled) setMarkets(data); })
      .catch(err => {
        if (!cancelled) {
          console.error('Failed to load markets', err);
          setLoadError('Não foi possível carregar a lista de mercados.');
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [isConnected]);

  useEffect(() => {
    if (!dropdownOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDropdownOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEsc);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEsc);
    };
  }, [dropdownOpen]);

  const handleSelect = (market: Market) => {
    setSelectedMarket(market);
    setDropdownOpen(false);
  };

  const handleRetryLoadMarkets = () => {
    setLoading(true);
    setLoadError(null);
    marketService.getMarkets()
      .then(data => setMarkets(data))
      .catch(err => {
        console.error('Failed to load markets', err);
        setLoadError('Não foi possível carregar a lista de mercados.');
      })
      .finally(() => setLoading(false));
  };

  return (
    <div
      className="p-4 space-y-5 pb-32"
      style={{ fontFamily: 'var(--font-body)', color: 'var(--color-text)' }}
    >
      {/* Header */}
      <div className="pt-2">
        <h1
          className="text-2xl font-bold"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
        >
          Início
        </h1>
        <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          Selecione o mercado e comece a escanear
        </p>
      </div>

      {/* Market Selector */}
      <div className="relative" ref={dropdownRef}>
        <p
          className="text-xs font-bold uppercase tracking-widest px-1 mb-1.5"
          style={{ color: 'var(--color-primary)', fontFamily: 'var(--font-body)' }}
        >
          Mercado
        </p>
        <button
          type="button"
          onClick={() => setDropdownOpen(o => !o)}
          aria-expanded={dropdownOpen}
          aria-haspopup="listbox"
          disabled={loading || !!loadError}
          className="w-full flex items-center justify-between p-4 rounded-xl cursor-pointer transition-all duration-200 active:opacity-80 disabled:cursor-not-allowed disabled:opacity-70"
          style={{
            backgroundColor: 'var(--color-surface)',
            border: `1px solid ${selectedMarket ? 'var(--color-primary)' : 'var(--color-border)'}`,
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="flex items-center justify-center w-10 h-10 rounded-xl shrink-0"
              style={{ backgroundColor: 'color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))' }}
            >
              <Store className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
            </div>
            <div className="min-w-0 text-left">
              {selectedMarket ? (
                <>
                  <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text)' }}>
                    {selectedMarket.name}
                  </p>
                  <p className="text-xs truncate" style={{ color: 'var(--color-text-muted)' }}>
                    {selectedMarket.address}
                  </p>
                </>
              ) : (
                <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                  {loading ? 'Carregando mercados...' : 'Toque para selecionar um mercado'}
                </p>
              )}
            </div>
          </div>
          <ChevronDown
            className="w-5 h-5 shrink-0 transition-transform duration-200"
            style={{
              color: 'var(--color-text-muted)',
              transform: dropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            }}
          />
        </button>

        {loadError && (
          <div
            className="mt-2 flex items-center justify-between gap-3 p-3 rounded-xl"
            style={{
              backgroundColor: 'color-mix(in srgb, var(--color-error) 5%, var(--color-surface))',
              border: '1px solid color-mix(in srgb, var(--color-error) 20%, var(--color-surface))',
            }}
          >
            <div className="flex items-center gap-2 min-w-0">
              <AlertCircle className="w-4 h-4 shrink-0" style={{ color: 'var(--color-error)' }} />
              <p className="text-xs font-medium truncate" style={{ color: 'var(--color-error)' }}>
                {loadError}
              </p>
            </div>
            <button
              type="button"
              onClick={handleRetryLoadMarkets}
              className="text-xs font-bold px-3 py-1 rounded-lg cursor-pointer shrink-0"
              style={{ backgroundColor: 'var(--color-error)', color: 'white' }}
            >
              Tentar novamente
            </button>
          </div>
        )}

        {/* Dropdown */}
        {dropdownOpen && (
          <div
            role="listbox"
            className="absolute left-0 right-0 mt-2 rounded-xl overflow-hidden z-20"
            style={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              boxShadow: 'var(--shadow-lg)',
              maxHeight: '280px',
              overflowY: 'auto',
            }}
          >
            {markets.map((market, idx) => {
              const isSelected = selectedMarket?.market_id === market.market_id;
              const isLast = idx === markets.length - 1;
              return (
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  key={market.market_id}
                  onClick={() => handleSelect(market)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left cursor-pointer transition-colors duration-150"
                  style={{
                    borderBottom: isLast ? 'none' : '1px solid var(--color-border)',
                    backgroundColor: isSelected ? 'color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))' : 'transparent',
                  }}
                  onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--color-bg-muted)')}
                  onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor =
                    isSelected ? 'color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))' : 'transparent'
                  )}
                >
                  <div
                    className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0"
                    style={{ backgroundColor: isSelected ? 'color-mix(in srgb, var(--color-primary) 12%, var(--color-surface))' : 'var(--color-bg-subtle)' }}
                  >
                    <Store className="w-4 h-4" style={{ color: isSelected ? 'var(--color-primary)' : 'var(--color-text-light-muted)' }} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text)' }}>
                      {market.name}
                    </p>
                    <p className="text-xs truncate flex items-center gap-1" style={{ color: 'var(--color-text-muted)' }}>
                      <MapPin className="w-3 h-3 shrink-0" />
                      {market.address}
                    </p>
                  </div>
                </button>
              );
            })}
            {markets.length === 0 && !loading && (
              <div className="px-4 py-6 text-center">
                <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Nenhum mercado disponível</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div
          className="rounded-xl p-4"
          style={{
            backgroundColor: 'var(--color-surface)',
            boxShadow: 'var(--shadow-md)',
            border: '1px solid var(--color-border)',
          }}
        >
          <div
            className="flex items-center justify-center w-9 h-9 rounded-lg mb-3"
            style={{ backgroundColor: 'color-mix(in srgb, var(--color-cta) 8%, var(--color-surface))' }}
          >
            <ScanBarcode className="w-5 h-5" style={{ color: 'var(--color-cta)' }} />
          </div>
          <p
            className="text-2xl font-bold"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-cta)' }}
          >
            {scanCount}
          </p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            Produtos Escaneados
          </p>
        </div>

        <div
          className="rounded-xl p-4"
          style={{
            backgroundColor: 'var(--color-surface)',
            boxShadow: 'var(--shadow-md)',
            border: '1px solid var(--color-border)',
          }}
        >
          <div
            className="flex items-center justify-center w-9 h-9 rounded-lg mb-3"
            style={{ backgroundColor: 'color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))' }}
          >
            <Store className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
          </div>
          <p
            className="text-lg font-bold truncate"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}
            title={selectedMarket?.name}
          >
            {selectedMarket ? selectedMarket.name : 'Nenhum'}
          </p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            Mercado Ativo
          </p>
        </div>
      </div>

      {/* CTA */}
      {selectedMarket && (
        <button
          type="button"
          onClick={() => navigate('/scanner')}
          className="w-full py-4 rounded-2xl text-sm font-bold flex items-center justify-center gap-2 cursor-pointer transition-all duration-200 active:scale-[0.98]"
          style={{
            backgroundColor: 'var(--color-cta)',
            color: 'white',
            fontFamily: 'var(--font-body)',
            boxShadow: '0 4px 14px rgba(249,115,22,0.3)',
          }}
        >
          <ScanBarcode className="w-5 h-5" />
          Começar a Escanear
        </button>
      )}

      {/* Recent Scans */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{
          backgroundColor: 'var(--color-surface)',
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div
          className="flex items-center justify-between px-4 py-3.5"
          style={{ borderBottom: '1px solid var(--color-border)' }}
        >
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 flex items-center justify-center rounded-lg"
            style={{ backgroundColor: 'color-mix(in srgb, var(--color-cta) 8%, var(--color-surface))' }}
          >
            <Barcode className="w-3.5 h-3.5" style={{ color: 'var(--color-cta)' }} />
            </div>
            <h2
              className="text-sm font-semibold"
              style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
            >
              Escaneamentos Recentes
            </h2>
          </div>
          {recentScans.length > 0 && (
            <span
              className="text-xs font-bold px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'color-mix(in srgb, var(--color-cta) 8%, var(--color-surface))', color: 'var(--color-cta)' }}
            >
              {recentScans.length}
            </span>
          )}
        </div>

        {recentScans.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 px-6 text-center">
            <div
              className="w-12 h-12 flex items-center justify-center rounded-2xl mb-3"
              style={{ backgroundColor: 'var(--color-bg-muted)' }}
            >
              <Barcode className="w-6 h-6" style={{ color: 'var(--color-icon-muted)' }} />
            </div>
            <p className="text-sm font-semibold" style={{ color: 'var(--color-text-muted)' }}>
              Nenhum escaneamento ainda
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-light-muted)' }}>
              Escaneie códigos de barras para vê-los aqui
            </p>
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
            {recentScans.slice(0, 10).map((scan, i) => (
              <div key={`${scan.ean}-${scan.savedAt}-${i}`} className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0"
                    style={{ backgroundColor: 'color-mix(in srgb, var(--color-success) 8%, var(--color-surface))' }}
                  >
                    <Barcode className="w-4 h-4" style={{ color: 'var(--color-success)' }} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-mono font-medium truncate" style={{ color: 'var(--color-text)' }}>
                      {scan.ean}
                    </p>
                    <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                      {new Date(scan.savedAt).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-bold" style={{ color: 'var(--color-cta)' }}>
                    R$ {scan.varejo_price.toFixed(2)}
                  </p>
                  {typeof scan.atacado_price === 'number' && (
                    <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                      Atacado: R$ {scan.atacado_price.toFixed(2)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;
