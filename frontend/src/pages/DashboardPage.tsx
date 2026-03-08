import React from 'react';
import { useStore } from '../store/useStore';
import {
  Loader2, CheckCircle2, XCircle, Clock,
  AlertCircle, ExternalLink,
  Receipt, Coins,
} from 'lucide-react';

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

const DashboardPage: React.FC = () => {
  const { processingQueue } = useStore();

  return (
    <div
      className="p-4 space-y-6"
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
        {/* Queue Header */}
        <div
          className="flex items-center justify-between px-4 py-4"
          style={{ borderBottom: '1px solid var(--color-border)' }}
        >
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
            <h2
              className="text-sm font-semibold"
              style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}
            >
              Fila de Processamento
            </h2>
          </div>
          {processingQueue.length > 0 && (
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{
                backgroundColor: '#EFF6FF',
                color: 'var(--color-primary)',
              }}
            >
              {processingQueue.length}
            </span>
          )}
        </div>

        {/* Queue Items */}
        <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
          {processingQueue.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
              <div
                className="w-12 h-12 flex items-center justify-center rounded-full mb-3"
                style={{ backgroundColor: '#F8FAFC' }}
              >
                <Clock className="w-6 h-6" style={{ color: '#CBD5E1' }} />
              </div>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                Nenhum processo ativo
              </p>
              <p className="text-xs mt-1" style={{ color: '#94A3B8' }}>
                Cupons escaneados aparecem aqui.
              </p>
            </div>
          ) : (
            processingQueue.map(item => (
              <QueueItem key={item.record_id} item={item} />
            ))
          )}
        </div>

        {processingQueue.length > 0 && (
          <div
            className="px-4 py-3 text-center"
            style={{ borderTop: '1px solid var(--color-border)' }}
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

const statusConfig: Record<string, { icon: React.ReactNode; label: string; bg: string; text: string; border: string }> = {
  success: {
    icon: <CheckCircle2 className="w-5 h-5" style={{ color: '#10B981' }} />,
    label: 'Concluído',
    bg: '#F0FDF4',
    text: '#166534',
    border: '#BBF7D0',
  },
  error: {
    icon: <XCircle className="w-5 h-5" style={{ color: '#EF4444' }} />,
    label: 'Erro',
    bg: '#FEF2F2',
    text: '#991B1B',
    border: '#FECACA',
  },
  duplicate: {
    icon: <AlertCircle className="w-5 h-5" style={{ color: '#F97316' }} />,
    label: 'Duplicado',
    bg: '#FFF7ED',
    text: '#9A3412',
    border: '#FED7AA',
  },
  pending: {
    icon: <Clock className="w-5 h-5" style={{ color: '#94A3B8' }} />,
    label: 'Pendente',
    bg: '#F8FAFC',
    text: '#475569',
    border: '#E2E8F0',
  },
};

const processingStatuses = new Set(['sending', 'queued', 'extracting', 'processing']);

interface QueueItemProps {
  item: {
    record_id: number;
    url: string;
    status: string;
    market_name?: string;
    products_count?: number;
    error_message?: string;
  };
}

const QueueItem: React.FC<QueueItemProps> = ({ item }) => {
  const isProcessing = processingStatuses.has(item.status);
  const config = statusConfig[item.status] ?? statusConfig.pending;

  const statusLabel =
    item.status === 'pending' ? 'Aguardando envio...' :
    item.status === 'sending' ? 'Enviando...' :
    item.status === 'queued' ? 'Na fila do servidor...' :
    item.status === 'extracting' ? 'Extraindo itens...' :
    config.label;

  return (
    <div
      className="px-4 py-3 flex items-start gap-3"
      style={{
        backgroundColor: isProcessing ? 'white' : config.bg,
        transition: 'background-color 200ms ease',
      }}
    >
      <div className="shrink-0 mt-0.5">
        {isProcessing ? (
          <Loader2 className="w-5 h-5 animate-spin" style={{ color: 'var(--color-primary)' }} />
        ) : (
          config.icon
        )}
      </div>

      <div className="flex-1 min-w-0">
        <p
          className="text-sm font-semibold truncate"
          style={{ color: config.text, fontFamily: 'var(--font-body)' }}
        >
          {item.market_name || statusLabel}
        </p>

        {item.status === 'error' && item.error_message && (
          <p className="text-xs mt-0.5 line-clamp-2" style={{ color: '#EF4444' }}>
            {item.error_message}
          </p>
        )}
        {item.status === 'duplicate' && (
          <p className="text-xs mt-0.5" style={{ color: '#F97316' }}>
            Este cupom já foi adicionado.
          </p>
        )}
        {item.products_count && item.status === 'success' && (
          <p className="text-xs mt-0.5 font-medium" style={{ color: 'var(--color-primary)' }}>
            {item.products_count} produtos extraídos
          </p>
        )}
        {!item.market_name && isProcessing && (
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            {statusLabel}
          </p>
        )}
      </div>

      {item.status === 'success' && (
        <button
          className="shrink-0 text-xs font-semibold flex items-center gap-0.5 cursor-pointer"
          style={{ color: '#10B981' }}
        >
          Ver <ExternalLink className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};

export default DashboardPage;
