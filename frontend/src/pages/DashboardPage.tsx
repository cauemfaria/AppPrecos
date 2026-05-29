import React from 'react';
import { useStore } from '../store/useStore';
import {
  CheckCircle2, XCircle, Clock,
  AlertCircle,
  Receipt, Coins, Store,
} from 'lucide-react';
import type { ProcessingItem } from '../types';

const STATS = [
  {
    label: 'Total Escaneados',
    value: '142',
    icon: Receipt,
    accent: 'var(--color-primary)',
    bg: 'color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))',
  },
  {
    label: 'Créditos',
    value: '85',
    icon: Coins,
    accent: 'var(--color-cta)',
    bg: 'color-mix(in srgb, var(--color-cta) 8%, var(--color-surface))',
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
    iconBg: 'color-mix(in srgb, var(--color-success) 10%, var(--color-surface))',
    iconColor: 'var(--color-success)',
    rowBg: 'color-mix(in srgb, var(--color-success) 5%, var(--color-surface))',
    textColor: 'var(--color-success)',
  },
  error: {
    label: (item: ProcessingItem) => item.market_name ?? domainFromUrl(item.url),
    sublabel: (item: ProcessingItem) => item.error_message ?? 'Erro ao processar',
    iconBg: 'color-mix(in srgb, var(--color-error) 10%, var(--color-surface))',
    iconColor: 'var(--color-error)',
    rowBg: 'color-mix(in srgb, var(--color-error) 5%, var(--color-surface))',
    textColor: 'var(--color-error)',
  },
  duplicate: {
    label: (item: ProcessingItem) => item.market_name ?? domainFromUrl(item.url),
    sublabel: () => 'Cupom já registrado',
    iconBg: 'color-mix(in srgb, var(--color-cta) 10%, var(--color-surface))',
    iconColor: 'var(--color-cta)',
    rowBg: 'color-mix(in srgb, var(--color-cta) 5%, var(--color-surface))',
    textColor: 'var(--color-cta)',
  },
  pending: {
    label: (item: ProcessingItem) => item.market_name ?? domainFromUrl(item.url),
    sublabel: () => 'Aguardando envio...',
    iconBg: 'var(--color-bg-subtle)',
    iconColor: 'var(--color-text-muted)',
    rowBg: 'var(--color-surface)',
    textColor: 'var(--color-text-muted)',
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
    ? (item.market_name ?? 'Na fila do servidor')
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
              style={{ backgroundColor: isActive ? 'color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))' : cfg.iconBg }}
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

    </div>
  );
};

// ─── DashboardPage ────────────────────────────────────────────────────────────

const DashboardPage: React.FC = () => {
  const { processingQueue: rawQueue } = useStore();
  const processingQueue = rawQueue.filter(item => item.status !== 'duplicate');

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
              style={{ backgroundColor: 'color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))' }}
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
                backgroundColor: 'color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))',
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
              style={{ backgroundColor: 'var(--color-bg-muted)' }}
            >
              <Clock className="w-6 h-6" style={{ color: 'var(--color-icon-muted)' }} />
            </div>
            <p className="text-sm font-semibold" style={{ color: 'var(--color-text-muted)' }}>
              Nenhum processo ativo
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-light-muted)' }}>
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
            style={{ borderTop: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-light)' }}
          >
            <p className="text-xs" style={{ color: 'var(--color-text-light-muted)' }}>
              Itens removidos automaticamente após conclusão
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
