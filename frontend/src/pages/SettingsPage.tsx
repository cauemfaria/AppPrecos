import React, { type ReactElement } from 'react';
import {
  User, LogOut, ChevronRight, Trash2, Sun, Moon,
  type LucideProps,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import { useAuthStore } from '../store/useAuthStore';
import { useTheme } from '../hooks/useTheme';
import { semanticColors } from '../utils/themeColors';

const SettingsPage: React.FC = () => {
  const { clearShoppingList, clearMarketSelection } = useStore();
  const { profile, user, signOut } = useAuthStore();
  const { theme, setTheme } = useTheme();

  const displayName = profile?.full_name || user?.email || 'Usuário Convidado';
  const displayEmail = user?.email || '';

  const handleClearData = () => {
    if (window.confirm('Tem certeza que deseja limpar todos os dados locais?')) {
      clearShoppingList();
      clearMarketSelection();
      alert('Dados locais limpos com sucesso.');
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
          Preferências e dados do app
        </p>
      </div>

      {/* CONTA */}
      <Section label="Conta">
        <SettingsItem
          icon={<User />}
          iconBg={semanticColors.iconBg.primary}
          iconColor={semanticColors.iconColor.primary}
          label={displayName}
          value={displayEmail}
          isLast
        />
      </Section>

      {/* ARMAZENAMENTO E DADOS */}
      <Section label="Armazenamento e Dados">
        <SettingsItem
          icon={<Trash2 />}
          iconBg={semanticColors.iconBg.error}
          iconColor={semanticColors.iconColor.error}
          label="Limpar Dados Locais"
          onClick={handleClearData}
          destructive
          isLast
        />
      </Section>

      {/* APARÊNCIA */}
      <Section label="Aparência">
        <div className="flex flex-col divide-y" style={{ borderColor: 'var(--color-border)' }}>
          {(['light', 'dark', 'system'] as const).map((mode, idx) => (
            <button
              key={mode}
              onClick={() => setTheme(mode)}
              className="w-full flex items-center justify-between px-4 py-3 transition-colors duration-150 cursor-pointer text-left hover:bg-opacity-50"
              style={{
                borderBottom: idx === 2 ? 'none' : '1px solid var(--color-border)',
              }}
              onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'color-mix(in srgb, var(--color-primary) 3%, var(--color-surface))')}
              onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'transparent')}
            >
              <div className="flex items-center gap-3">
                <div
                  className="flex items-center justify-center w-8 h-8 rounded-lg"
                  style={{ backgroundColor: semanticColors.iconBg.primary }}
                >
                  {mode === 'light' ? (
                    <Sun size={16} style={{ color: semanticColors.iconColor.primary }} />
                  ) : mode === 'dark' ? (
                    <Moon size={16} style={{ color: semanticColors.iconColor.primary }} />
                  ) : (
                    <div style={{ color: semanticColors.iconColor.primary, fontSize: '16px' }}>◐</div>
                  )}
                </div>
                <span className="text-sm font-medium" style={{ color: 'var(--color-text)' }}>
                  {mode === 'light' ? 'Claro' : mode === 'dark' ? 'Escuro' : 'Sistema'}
                </span>
              </div>
              {theme === mode && (
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: 'var(--color-primary)' }}
                />
              )}
            </button>
          ))}
        </div>
      </Section>

      {/* Sign out */}
      <button
        onClick={() => signOut()}
        className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-sm cursor-pointer transition-all duration-200 hover:opacity-80"
        style={{
          backgroundColor: 'color-mix(in srgb, var(--color-error) 5%, var(--color-surface))',
          color: 'var(--color-error)',
          border: '1px solid color-mix(in srgb, var(--color-error) 20%, var(--color-surface))',
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
}) => (
  <button
    onClick={onClick}
    className="w-full flex items-center justify-between px-4 py-3 transition-colors duration-150 cursor-pointer"
    style={{
      borderBottom: isLast ? 'none' : '1px solid var(--color-border)',
      fontFamily: 'var(--font-body)',
    }}
    onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = '#F8FAFC')}
    onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'transparent')}
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
          className="text-xs font-medium"
          style={{ color: valueColor || 'var(--color-text-muted)' }}
        >
          {value}
        </span>
      )}
      <ChevronRight className="w-4 h-4" style={{ color: '#CBD5E1' }} />
    </div>
  </button>
);

export default SettingsPage;
