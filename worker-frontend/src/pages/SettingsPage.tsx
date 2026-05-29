import React, { type ReactElement } from 'react';
import {
  User, LogOut, ChevronRight, Trash2, Store,
  type LucideProps,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import { useAuthStore } from '../store/useAuthStore';

const SettingsPage: React.FC = () => {
  const { selectedMarket, setSelectedMarket, clearScans, recentScans, scanCount } = useStore();
  const { profile, user, signOut } = useAuthStore();

  const displayName = profile?.full_name || user?.email || 'Colaborador';
  const displayEmail = user?.email || '';

  const handleClearMarket = () => {
    if (window.confirm('Deseja remover o mercado selecionado?')) {
      setSelectedMarket(null);
    }
  };

  const handleClearScans = () => {
    if (recentScans.length === 0 && scanCount === 0) {
      alert('Nenhum dado para limpar.');
      return;
    }
    if (window.confirm('Tem certeza que deseja apagar o histórico de escaneamentos e zerar o contador?')) {
      clearScans();
    }
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
          Configurações
        </h1>
        <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          Preferências do aplicativo
        </p>
      </div>

      {/* CONTA */}
      <Section label="Conta">
        <SettingsItem
          icon={<User />}
          iconBg="#EFF6FF"
          iconColor="var(--color-primary)"
          label={displayName}
          value={displayEmail}
          isLast
        />
      </Section>

      {/* DADOS LOCAIS */}
      <Section label="Dados Locais">
        <SettingsItem
          icon={<Store />}
          iconBg="#EFF6FF"
          iconColor="var(--color-primary)"
          label="Mercado Selecionado"
          value={selectedMarket ? selectedMarket.name : 'Nenhum'}
          onClick={selectedMarket ? handleClearMarket : undefined}
        />
        <SettingsItem
          icon={<Trash2 />}
          iconBg="#FEF2F2"
          iconColor="#EF4444"
          label="Limpar Histórico de Escaneamentos"
          onClick={handleClearScans}
          destructive
          isLast
        />
      </Section>

      {/* Sign out */}
      <button
        onClick={() => signOut()}
        className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-sm cursor-pointer transition-all duration-200 hover:opacity-80"
        style={{
          backgroundColor: '#FEF2F2',
          color: '#DC2626',
          border: '1px solid #FECACA',
          fontFamily: 'var(--font-body)',
        }}
      >
        <LogOut className="w-4 h-4" />
        Sair
      </button>
    </div>
  );
};

const Section: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <section className="space-y-1.5">
    <p
      className="text-xs font-bold uppercase tracking-widest px-1"
      style={{ color: 'var(--color-primary)', fontFamily: 'var(--font-body)' }}
    >
      {label}
    </p>
    <div
      className="overflow-hidden rounded-xl"
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      {children}
    </div>
  </section>
);

interface SettingsItemProps {
  icon: ReactElement<LucideProps>;
  iconBg: string;
  iconColor: string;
  label: string;
  value?: string;
  valueColor?: string;
  isLast?: boolean;
  onClick?: () => void;
  destructive?: boolean;
}

const SettingsItem: React.FC<SettingsItemProps> = ({
  icon, iconBg, iconColor, label, value, valueColor, isLast, onClick, destructive,
}) => {
  const interactive = !!onClick;
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!interactive}
      className="w-full flex items-center justify-between px-4 py-3 transition-colors duration-150 disabled:cursor-default cursor-pointer text-left"
      style={{
        borderBottom: isLast ? 'none' : '1px solid var(--color-border)',
        fontFamily: 'var(--font-body)',
        backgroundColor: 'transparent',
      }}
      onMouseEnter={e => {
        if (interactive) (e.currentTarget as HTMLElement).style.backgroundColor = '#F8FAFC';
      }}
      onMouseLeave={e => {
        if (interactive) (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
      }}
    >
      <div className="flex items-center gap-3">
        <div
          className="flex items-center justify-center w-8 h-8 rounded-lg"
          style={{ backgroundColor: iconBg }}
        >
          {React.cloneElement(icon, {
            size: 16,
            style: { color: iconColor },
          } as LucideProps & { style: React.CSSProperties })}
        </div>
        <span
          className="text-sm font-medium"
          style={{ color: destructive ? '#DC2626' : 'var(--color-text)', fontFamily: 'var(--font-body)' }}
        >
          {label}
        </span>
      </div>
      <div className="flex items-center gap-2">
        {value && (
          <span
            className="text-xs font-medium truncate max-w-[140px]"
            style={{ color: valueColor || 'var(--color-text-muted)' }}
          >
            {value}
          </span>
        )}
        <ChevronRight className="w-4 h-4 shrink-0" style={{ color: '#CBD5E1' }} />
      </div>
    </button>
  );
};

export default SettingsPage;
