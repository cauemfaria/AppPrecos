import React from 'react';
import { useStore } from '../store/useStore';
import {
  CheckCircle2, XCircle, Clock,
  AlertCircle, ExternalLink,
  Receipt, Coins, Store,
} from 'lucide-react';
import type { ProcessingItem } from '../types';

const STATS = [
  {
    label: 'Total Escaneados',
    value: '142',
    icon: Receipt,
    accent: 'var(--color-primary)',
    bg: '#EFF6FF',
  },
  {
    label: 'Créditos',
    value: '85',
    icon: Coins,
    accent: 'var(--color-cta)',
    bg: '#FFF7ED',
  },
];

// Extract a short readable label from a NFCe URL
const domainFromUrl = (url: string) => {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return 'Cupom';
  }
};

// ─── Status config ────────────────────────────────────────────────────────────

type StatusKey = 'success' | 'error' | 'duplicate' | 'pending';

const statusConfig: Record<StatusKey, {
  label: (item: ProcessingItem) => string;
  sublabel: (item: ProcessingItem) => string;
  iconBg: string;
  iconColor: string;
  rowBg: string;
  textColor: string;
}> = {
  success: {
    label: (item: ProcessingItem) => item.market_name ?? 'Concluído',
    sublabel: (item: ProcessingItem) => item.products_count ? `${item.products_count} produto${item.products_count !== 1 ? 's' : ''} extraído${item.products_count !== 1 ? 's' : ''}` : 'Processado com sucesso',
    iconBg: '#DCFCE7',
    iconColor: '#16A34A',
    rowBg: '#F0FDF4',
    textColor: '#166534',
  },
  error: {
    label: (item: ProcessingItem) => item.market_name ?? domainFromUrl(item.url),
    sublabel: (item: ProcessingItem) => item.error_message ?? 'Erro ao processar',
    iconBg: '#FEE2E2',
    iconColor: '#DC2626',
    rowBg: '#FEF2F2',
    textColor: '#991B1B',
  },
  duplicate: {
    label: (item: ProcessingItem) => item.market_name ?? domainFromUrl(item.url),
    sublabel: () => 'Cupom já registrado',
    iconBg: '#FEF3C7',
    iconColor: '#D97706',
    rowBg: '#FFFBEB',
    textColor: '#92400E',
  },
  pending: {
    label: (item: ProcessingItem) => item.market_name ?? domainFromUrl(item.url),
    sublabel: () => 'Aguardando envio...',
    iconBg: '#F1F5F9',
    iconColor: '#94A3B8',
    rowBg: '#FFFFFF',
    textColor: '#475569',
  },
};

// Statuses that are "in progress" (spinner)
const processingStatuses = new Set(['sending', 'queued', 'extracting', 'processing']);

// Human-readable processing label per status
const processingLabel: Record<string, string> = {
  pending: 'Aguardando envio…',
  sending: 'Enviando…',
  queued: 'Na fila do servidor…',
  extracting: 'Extraindo produtos…',
  processing: 'Processando…',
};

// ─── QueueItem ────────────────────────────────────────────────────────────────

const QueueItem: React.FC<{ item: ProcessingItem }> = ({ item }) => {
  const isActive = processingStatuses.has(item.status);

  // Resolve config — active statuses use the 'pending' base style
  const cfgKey = (isActive ? 'pending' : item.status) as StatusKey;
  const cfg = statusConfig[cfgKey] ?? statusConfig.pending;

  const primaryText = isActive
    ? (item.market_name ?? domainFromUrl(item.url))
    : cfg.label(item);

  const secondaryText = isActive
    ? processingLabel[item.status] ?? 'Processando…'
    : cfg.sublabel(item);

  return (
    <div
      className="flex items-center gap-3 px-4 py-3"
      style={{
        backgroundColor: cfg.rowBg,
        transition: 'background-color 200ms ease',
      }}
    >
      {/* Icon */}
      <div
        className="shrink-0 w-9 h-9 flex items-center justify-center rounded-xl"
        style={{ backgroundColor: isActive ? '#EFF6FF' : cfg.iconBg }}
      >
        {isActive ? (
          <svg
            className="w-5 h-5 animate-spin"
            style={{ color: 'var(--color-primary)' }}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
        ) : item.status === 'success' ? (
          <CheckCircle2 className="w-5 h-5" style={{ color: cfg.iconColor }} />
        ) : item.status === 'error' ? (
          <XCircle className="w-5 h-5" style={{ color: cfg.iconColor }} />
        ) : item.status === 'duplicate' ? (
          <AlertCircle className="w-5 h-5" style={{ color: cfg.iconColor }} />
        ) : (
          <Store className="w-5 h-5" style={{ color: cfg.iconColor }} />
        )}
      </div>

      {/* Text */}
      <div className="flex-1 min-w-0">
        <p
          className="text-sm font-semibold truncate leading-tight"
          style={{
            color: isActive ? 'var(--color-text)' : cfg.textColor,
            fontFamily: 'var(--font-body)',
          }}
        >
          {primaryText}
        </p>
        <p
          className="text-xs mt-0.5 truncate"
          style={{
            color: isActive ? 'var(--color-text-muted)' : cfg.textColor,
            opacity: isActive ? 1 : 0.75,
            fontFamily: 'var(--font-body)',
          }}
        >
          {secondaryText}
        </p>
      </div>

      {/* Action */}
      {item.status === 'success' && (
        <button
          className="shrink-0 flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg cursor-pointer transition-all duration-150 active:scale-95"
          style={{
            color: '#16A34A',
            backgroundColor: '#DCFCE7',
            fontFamily: 'var(--font-body)',
          }}
        >
          Ver <ExternalLink className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};

// ─── DashboardPage ────────────────────────────────────────────────────────────

const DashboardPage: React.FC = () => {
  const { processingQueue } = useStore();

  return (
    <div
      className="p-4 space-y-5"
      style={{ fontFamily: 'var(--font-body)', color: 'var(--color-text)' }}
    >
      {/* Page Header */}
      <div className="pt-2">
        <h1
          className="text-2xl font-bold"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
        >
          Início
        </h1>
        <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          Resumo da sua atividade
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        {STATS.map(({ label, value, icon: Icon, accent, bg }) => (
          <div
            key={label}
            className="rounded-xl p-4"
            style={{
              backgroundColor: 'var(--color-surface)',
              boxShadow: 'var(--shadow-md)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div
              className="flex items-center justify-center w-9 h-9 rounded-lg mb-3"
              style={{ backgroundColor: bg }}
            >
              <Icon className="w-5 h-5" style={{ color: accent }} />
            </div>
            <p
              className="text-2xl font-bold"
              style={{ fontFamily: 'var(--font-heading)', color: accent }}
            >
              {value}
            </p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
              {label}
            </p>
          </div>
        ))}
      </div>

      {/* Processing Queue */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{
          backgroundColor: 'var(--color-surface)',
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--color-border)',
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-4 py-3.5"
          style={{ borderBottom: '1px solid var(--color-border)' }}
        >
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 flex items-center justify-center rounded-lg"
              style={{ backgroundColor: '#EFF6FF' }}
            >
              <Clock className="w-3.5 h-3.5" style={{ color: 'var(--color-primary)' }} />
            </div>
            <h2
              className="text-sm font-semibold"
              style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
            >
              Fila de Processamento
            </h2>
          </div>
          {processingQueue.length > 0 && (
            <span
              className="text-xs font-bold px-2 py-0.5 rounded-full"
              style={{
                backgroundColor: '#EFF6FF',
                color: 'var(--color-primary)',
              }}
            >
              {processingQueue.length}
            </span>
          )}
        </div>

        {/* Items */}
        {processingQueue.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 px-6 text-center">
            <div
              className="w-12 h-12 flex items-center justify-center rounded-2xl mb-3"
              style={{ backgroundColor: '#F8FAFC' }}
            >
              <Clock className="w-6 h-6" style={{ color: '#CBD5E1' }} />
            </div>
            <p className="text-sm font-semibold" style={{ color: 'var(--color-text-muted)' }}>
              Nenhum processo ativo
            </p>
            <p className="text-xs mt-1" style={{ color: '#94A3B8' }}>
              Cupons escaneados aparecem aqui
            </p>
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
            {processingQueue.map(item => (
              <QueueItem key={item.record_id} item={item} />
            ))}
          </div>
        )}

        {/* Footer hint */}
        {processingQueue.length > 0 && (
          <div
            className="px-4 py-2.5 text-center"
            style={{ borderTop: '1px solid var(--color-border)', backgroundColor: '#FAFAFA' }}
          >
            <p className="text-xs" style={{ color: '#94A3B8' }}>
              Itens removidos automaticamente após conclusão
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
