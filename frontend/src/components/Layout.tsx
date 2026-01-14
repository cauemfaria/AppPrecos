import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Scan, Store, ShoppingBasket, Settings } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const Layout: React.FC = () => {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50 pb-20 md:pb-0 md:pl-64">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-white border-r border-gray-200 fixed h-full left-0 top-0 z-50">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-blue-600 flex items-center gap-2">
            <ShoppingBasket className="w-8 h-8" />
            AppPrecos
          </h1>
        </div>
        
        <nav className="flex-1 px-4 py-4 space-y-2">
          <DesktopNavLink to="/" icon={<Scan />} label="Scanner" />
          <DesktopNavLink to="/markets" icon={<Store />} label="Markets" />
          <DesktopNavLink to="/shopping-list" icon={<ShoppingBasket />} label="Shopping List" />
          <DesktopNavLink to="/settings" icon={<Settings />} label="Settings" />
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto">
          <Outlet />
        </div>
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-6 py-3 flex justify-between items-center z-50 shadow-lg">
        <MobileNavLink to="/" icon={<Scan />} label="Scanner" />
        <MobileNavLink to="/markets" icon={<Store />} label="Markets" />
        <MobileNavLink to="/shopping-list" icon={<ShoppingBasket />} label="List" />
        <MobileNavLink to="/settings" icon={<Settings />} label="Settings" />
      </nav>
    </div>
  );
};

interface NavLinkProps {
  to: string;
  icon: React.ReactNode;
  label: string;
}

const DesktopNavLink: React.FC<NavLinkProps> = ({ to, icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      cn(
        "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 font-medium",
        isActive 
          ? "bg-blue-50 text-blue-600 shadow-sm" 
          : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
      )
    }
  >
    {React.cloneElement(icon as React.ReactElement, { className: "w-5 h-5" })}
    {label}
  </NavLink>
);

const MobileNavLink: React.FC<NavLinkProps> = ({ to, icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      cn(
        "flex flex-col items-center gap-1 transition-all duration-200",
        isActive ? "text-blue-600" : "text-gray-400"
      )
    }
  >
    <div className={cn(
      "p-2 rounded-full transition-all duration-200",
      "active:scale-90"
    )}>
      {React.cloneElement(icon as React.ReactElement, { className: "w-6 h-6" })}
    </div>
    <span className="text-[10px] font-medium uppercase tracking-wider">{label}</span>
  </NavLink>
);

export default Layout;
