import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Store, ScanBarcode, ChevronDown, Barcode, MapPin } from 'lucide-react';
import { useStore } from '../store/useStore';
import { marketService } from '../services/api';
import type { Market } from '../types';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedMarket, setSelectedMarket, scanCount, recentScans } = useStore();
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    marketService.getMarkets()
      .then(setMarkets)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = (market: Market) => {
    setSelectedMarket(market);
    setDropdownOpen(false);
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
      <div className="relative">
        <p
          className="text-xs font-bold uppercase tracking-widest px-1 mb-1.5"
          style={{ color: 'var(--color-primary)', fontFamily: 'var(--font-body)' }}
        >
          Mercado
        </p>
        <button
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="w-full flex items-center justify-between p-4 rounded-xl cursor-pointer transition-all duration-200 active:opacity-80"
          style={{
            backgroundColor: 'var(--color-surface)',
            border: `1px solid ${selectedMarket ? 'var(--color-primary)' : 'var(--color-border)'}`,
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="flex items-center justify-center w-10 h-10 rounded-xl shrink-0"
              style={{ backgroundColor: '#EFF6FF' }}
            >
              <Store className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
            </div>
            <div className="min-w-0">
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

        {/* Dropdown */}
        {dropdownOpen && (
          <div
            className="absolute left-0 right-0 mt-2 rounded-xl overflow-hidden z-20"
            style={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              boxShadow: 'var(--shadow-lg)',
              maxHeight: '280px',
              overflowY: 'auto',
            }}
          >
            {markets.map((market) => (
              <button
                key={market.market_id}
                onClick={() => handleSelect(market)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left cursor-pointer transition-colors duration-150"
                style={{
                  borderBottom: '1px solid var(--color-border)',
                  backgroundColor: selectedMarket?.market_id === market.market_id ? '#EFF6FF' : 'transparent',
                }}
                onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = '#F8FAFC')}
                onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor =
                  selectedMarket?.market_id === market.market_id ? '#EFF6FF' : 'transparent'
                )}
              >
                <div
                  className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0"
                  style={{ backgroundColor: selectedMarket?.market_id === market.market_id ? '#DBEAFE' : '#F1F5F9' }}
                >
                  <Store className="w-4 h-4" style={{ color: selectedMarket?.market_id === market.market_id ? 'var(--color-primary)' : '#94A3B8' }} />
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
            ))}
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
            style={{ backgroundColor: '#FFF7ED' }}
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
            style={{ backgroundColor: '#EFF6FF' }}
          >
            <Store className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
          </div>
          <p
            className="text-lg font-bold truncate"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}
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
              style={{ backgroundColor: '#FFF7ED' }}
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
              style={{ backgroundColor: '#FFF7ED', color: 'var(--color-cta)' }}
            >
              {recentScans.length}
            </span>
          )}
        </div>

        {recentScans.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 px-6 text-center">
            <div
              className="w-12 h-12 flex items-center justify-center rounded-2xl mb-3"
              style={{ backgroundColor: '#F8FAFC' }}
            >
              <Barcode className="w-6 h-6" style={{ color: '#CBD5E1' }} />
            </div>
            <p className="text-sm font-semibold" style={{ color: 'var(--color-text-muted)' }}>
              Nenhum escaneamento ainda
            </p>
            <p className="text-xs mt-1" style={{ color: '#94A3B8' }}>
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
                    style={{ backgroundColor: '#F0FDF4' }}
                  >
                    <Barcode className="w-4 h-4" style={{ color: '#16A34A' }} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-mono font-medium" style={{ color: 'var(--color-text)' }}>
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
                  {scan.atacado_price && (
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
