import React, { type ReactElement, useState } from 'react';
import {
  User, Bell, Shield,
  HelpCircle, Info, LogOut, ChevronRight,
  Github, Globe, Heart, type LucideProps,
  Trash2, Database, Sparkles, Loader2,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import { enrichmentService } from '../services/api';

const SettingsPage: React.FC = () => {
  const { clearShoppingList, clearMarketSelection } = useStore();
  const [isEnriching, setIsEnriching] = useState(false);

  const handleClearData = () => {
    if (window.confirm('Tem certeza que deseja limpar todos os dados locais?')) {
      clearShoppingList();
      clearMarketSelection();
      alert('Dados locais limpos com sucesso.');
    }
  };

  const handleTriggerEnrichment = async () => {
    setIsEnriching(true);
    try {
      const response = await enrichmentService.triggerEnrichment();
      alert(response.message);
    } catch (error: any) {
      alert('Falha ao iniciar sincronização: ' + (error.response?.data?.error || error.message));
    } finally {
      setIsEnriching(false);
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
          iconBg="#EFF6FF"
          iconColor="var(--color-primary)"
          label="Perfil"
          value="Usuário Convidado"
        />
        <SettingsItem
          icon={<Bell />}
          iconBg="#FFF7ED"
          iconColor="var(--color-cta)"
          label="Notificações"
        />
        <SettingsItem
          icon={<Shield />}
          iconBg="#F0FDF4"
          iconColor="#16A34A"
          label="Privacidade e Segurança"
          isLast
        />
      </Section>

      {/* ARMAZENAMENTO E DADOS */}
      <Section label="Armazenamento e Dados">
        <SettingsItem
          icon={isEnriching ? <Loader2 className="animate-spin" /> : <Sparkles />}
          iconBg="#EFF6FF"
          iconColor="var(--color-primary)"
          label="Sincronizar Dados"
          value={isEnriching ? 'Processando...' : 'Iniciar'}
          onClick={handleTriggerEnrichment}
        />
        <SettingsItem
          icon={<Trash2 />}
          iconBg="#FEF2F2"
          iconColor="#EF4444"
          label="Limpar Dados Locais"
          onClick={handleClearData}
          destructive
        />
        <SettingsItem
          icon={<Database />}
          iconBg="#F8FAFC"
          iconColor="#64748B"
          label="Status do Banco de Dados"
          value="Online"
          valueColor="#16A34A"
          isLast
        />
      </Section>

      {/* APLICATIVO */}
      <Section label="Aplicativo">
        <SettingsItem
          icon={<Globe />}
          iconBg="#F5F3FF"
          iconColor="#7C3AED"
          label="Idioma"
          value="Português (BR)"
        />
        <SettingsItem
          icon={<Info />}
          iconBg="#EFF6FF"
          iconColor="var(--color-secondary)"
          label="Versão"
          value="1.0.0 (Web)"
        />
        <SettingsItem
          icon={<Github />}
          iconBg="#F1F5F9"
          iconColor="#334155"
          label="Código Fonte"
          isLast
        />
      </Section>

      {/* SUPORTE */}
      <Section label="Suporte">
        <SettingsItem
          icon={<HelpCircle />}
          iconBg="#F0FDF4"
          iconColor="#0D9488"
          label="Central de Ajuda"
        />
        <SettingsItem
          icon={<Heart />}
          iconBg="#FEF2F2"
          iconColor="#EF4444"
          label="Sobre o EconomiX"
          isLast
        />
      </Section>

      {/* Sign out */}
      <button
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
