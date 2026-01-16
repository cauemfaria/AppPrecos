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
    if (window.confirm("Are you sure you want to clear all local app data? This will empty your shopping list and market selections.")) {
      clearShoppingList();
      clearMarketSelection();
      alert("Local data cleared successfully.");
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold mb-6">Settings</h2>

      <div className="space-y-6 pb-20">
        {/* Account Section */}
        <section className="space-y-2">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-4">Account</h3>
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <SettingsItem icon={<User className="text-blue-500" />} label="Profile" value="Guest User" />
            <SettingsItem icon={<Bell className="text-orange-500" />} label="Notifications" />
            <SettingsItem icon={<Shield className="text-green-500" />} label="Privacy & Security" />
          </div>
        </section>

        {/* Storage Section */}
        <section className="space-y-2">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-4">Storage & Data</h3>
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <SettingsItem 
              icon={<Trash2 className="text-red-500" />} 
              label="Clear Local Data" 
              onClick={handleClearData}
            />
            <SettingsItem icon={<Database className="text-gray-500" />} label="Database Status" value="Online" isLast />
          </div>
        </section>

        {/* App Section */}
        <section className="space-y-2">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-4">Application</h3>
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <SettingsItem icon={<Globe className="text-purple-500" />} label="Language" value="Portuguese (BR)" />
            <SettingsItem icon={<Info className="text-blue-400" />} label="Version" value="1.0.0 (Web)" />
            <SettingsItem icon={<Github className="text-gray-700" />} label="Source Code" />
          </div>
        </section>

        {/* Support Section */}
        <section className="space-y-2">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-4">Support</h3>
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <SettingsItem icon={<HelpCircle className="text-teal-500" />} label="Help Center" />
            <SettingsItem icon={<Heart className="text-red-500" />} label="About AppPrecos" isLast />
          </div>
        </section>

        <button className="w-full bg-red-50 text-red-600 font-bold py-4 rounded-3xl flex items-center justify-center gap-2 hover:bg-red-100 transition-colors">
          <LogOut className="w-5 h-5" />
          Log Out
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
