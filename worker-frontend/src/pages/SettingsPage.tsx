import React, { type ReactElement } from 'react';
import {
  User, Bell, Shield,
  HelpCircle, Info,
  Globe, Heart, type LucideProps,
  ChevronRight, Database,
} from 'lucide-react';

const SettingsPage: React.FC = () => {
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
          label="Perfil"
          value="Colaborador"
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
          icon={<Database />}
          iconBg="#F8FAFC"
          iconColor="#64748B"
          label="Status do Banco de Dados"
          value="Online"
          valueColor="#16A34A"
        />
        <SettingsItem
          icon={<Info />}
          iconBg="#EFF6FF"
          iconColor="var(--color-secondary)"
          label="Versão"
          value="1.0.0 (Worker)"
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
          label="Sobre o EconomiX Worker"
          isLast
        />
      </Section>
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
}

const SettingsItem: React.FC<SettingsItemProps> = ({
  icon, iconBg, iconColor, label, value, valueColor, isLast,
}) => (
  <div
    className="w-full flex items-center justify-between px-4 py-3"
    style={{
      borderBottom: isLast ? 'none' : '1px solid var(--color-border)',
      fontFamily: 'var(--font-body)',
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
        style={{ color: 'var(--color-text)', fontFamily: 'var(--font-body)' }}
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
  </div>
);

export default SettingsPage;
