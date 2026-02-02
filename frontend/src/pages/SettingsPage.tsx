import React, { type ReactElement } from 'react';
import { 
  User, Bell, Shield, 
  HelpCircle, Info, LogOut, ChevronRight,
  Github, Globe, Heart, type LucideProps, Trash2, Database
} from 'lucide-react';
import { useStore } from '../store/useStore';

const SettingsPage: React.FC = () => {
  const { clearShoppingList, clearMarketSelection } = useStore();

  const handleClearData = () => {
    if (window.confirm("Tem certeza que deseja limpar todos os dados locais do app? Isso esvaziará sua lista de compras e seleções de mercado.")) {
      clearShoppingList();
      clearMarketSelection();
      alert("Dados locais limpos com sucesso.");
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold mb-6">Configurações</h2>

      <div className="space-y-6 pb-20">
        {/* Account Section */}
        <section className="space-y-2">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-4">Conta</h3>
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <SettingsItem icon={<User className="text-blue-500" />} label="Perfil" value="Usuário Convidado" />
            <SettingsItem icon={<Bell className="text-orange-500" />} label="Notificações" />
            <SettingsItem icon={<Shield className="text-green-500" />} label="Privacidade e Segurança" />
          </div>
        </section>

        {/* Storage Section */}
        <section className="space-y-2">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-4">Armazenamento e Dados</h3>
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <SettingsItem 
              icon={<Trash2 className="text-red-500" />} 
              label="Limpar Dados Locais" 
              onClick={handleClearData}
            />
            <SettingsItem icon={<Database className="text-gray-500" />} label="Status do Banco de Dados" value="Online" isLast />
          </div>
        </section>

        {/* App Section */}
        <section className="space-y-2">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-4">Aplicativo</h3>
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <SettingsItem icon={<Globe className="text-purple-500" />} label="Idioma" value="Português (BR)" />
            <SettingsItem icon={<Info className="text-blue-400" />} label="Versão" value="1.0.0 (Web)" />
            <SettingsItem icon={<Github className="text-gray-700" />} label="Código Fonte" />
          </div>
        </section>

        {/* Support Section */}
        <section className="space-y-2">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-4">Suporte</h3>
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <SettingsItem icon={<HelpCircle className="text-teal-500" />} label="Central de Ajuda" />
            <SettingsItem icon={<Heart className="text-red-500" />} label="Sobre o AppPrecos" isLast />
          </div>
        </section>

        <button className="w-full bg-red-50 text-red-600 font-bold py-4 rounded-3xl flex items-center justify-center gap-2 hover:bg-red-100 transition-colors">
          <LogOut className="w-5 h-5" />
          Sair
        </button>
      </div>
    </div>
  );
};

interface SettingsItemProps {
  icon: ReactElement<LucideProps>;
  label: string;
  value?: string;
  isLast?: boolean;
  onClick?: () => void;
}

const SettingsItem: React.FC<SettingsItemProps> = ({ icon, label, value, isLast, onClick }) => (
  <button 
    onClick={onClick}
    className={`w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors ${!isLast ? 'border-b border-gray-50' : ''}`}
  >
    <div className="flex items-center gap-4">
      <div className="p-2 bg-gray-50 rounded-xl">
        {React.cloneElement(icon, { size: 20 })}
      </div>
      <span className="font-bold text-gray-700">{label}</span>
    </div>
    <div className="flex items-center gap-2">
      {value && <span className="text-sm text-gray-400 font-medium">{value}</span>}
      <ChevronRight className="w-5 h-5 text-gray-300" />
    </div>
  </button>
);

export default SettingsPage;
