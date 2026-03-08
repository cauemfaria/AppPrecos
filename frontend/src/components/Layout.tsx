import React, { type ReactElement } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Home, Store, ShoppingBasket, Settings, QrCode, type LucideProps } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div
      className="flex flex-col min-h-screen pb-24 md:pb-0 md:pl-64"
      style={{ backgroundColor: 'var(--color-background)', fontFamily: 'var(--font-body)' }}
    >
      {/* Desktop Sidebar */}
      <aside
        className="hidden md:flex flex-col w-64 fixed h-full left-0 top-0 z-50"
        style={{ backgroundColor: 'var(--color-surface)', borderRight: '1px solid var(--color-border)' }}
      >
        <div className="p-6" style={{ borderBottom: '1px solid var(--color-border)' }}>
          <div
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <div className="w-9 h-9 rounded-xl overflow-hidden flex items-center justify-center" style={{ backgroundColor: '#EFF6FF' }}>
              <img 
                src="/app-logo.png" 
                alt="AppPrecos Logo" 
                className="w-full h-full object-contain object-center"
              />
            </div>
            <h1
              className="text-xl font-bold"
              style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}
            >
              EconomiX
            </h1>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <DesktopNavLink to="/" icon={<Home />} label="Início" exact />
          <DesktopNavLink to="/markets" icon={<Store />} label="Mercados" />
          <DesktopNavLink to="/scanner" icon={<QrCode />} label="Escanear NFCe" />
          <DesktopNavLink to="/shopping-list" icon={<ShoppingBasket />} label="Lista de Compras" />
          <DesktopNavLink to="/settings" icon={<Settings />} label="Configurações" />
        </nav>

        <div className="p-4" style={{ borderTop: '1px solid var(--color-border)' }}>
          <p
            className="text-xs"
            style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-body)' }}
          >
            Economize no Mercado
          </p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto">
          <Outlet />
        </div>
      </main>

      {/* Mobile Bottom Navigation */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 z-50"
        style={{
          backgroundColor: 'var(--color-surface)',
          borderTop: '1px solid var(--color-border)',
          boxShadow: '0 -2px 12px rgba(0,0,0,0.06)',
        }}
      >
        <div className="flex items-end justify-around px-2 pt-2 pb-6">
          <MobileNavLink to="/" icon={<Home />} label="Início" exact />
          <MobileNavLink to="/markets" icon={<Store />} label="Mercados" />

          {/* Center QR Scan Button */}
          <div className="flex flex-col items-center -mt-5">
            <button
              onClick={() => navigate('/scanner')}
              className="flex items-center justify-center w-14 h-14 rounded-full cursor-pointer transition-all duration-200 active:scale-95"
              style={{
                backgroundColor: location.pathname === '/scanner' ? 'var(--color-primary)' : 'var(--color-cta)',
                boxShadow: '0 4px 14px rgba(249,115,22,0.4)',
              }}
              aria-label="Escanear NFCe"
            >
              <QrCode className="w-6 h-6 text-white" />
            </button>
            <span
              className="text-xs mt-1 font-medium"
              style={{
                color: location.pathname === '/scanner' ? 'var(--color-primary)' : 'var(--color-text-muted)',
                fontFamily: 'var(--font-body)',
              }}
            >
              Scan
            </span>
          </div>

          <MobileNavLink to="/shopping-list" icon={<ShoppingBasket />} label="Lista" />
          <MobileNavLink to="/settings" icon={<Settings />} label="Ajustes" />
        </div>
      </nav>
    </div>
  );
};

interface NavLinkProps {
  to: string;
  icon: ReactElement<LucideProps>;
  label: string;
  exact?: boolean;
}

const DesktopNavLink: React.FC<NavLinkProps> = ({ to, icon, label, exact }) => (
  <NavLink
    to={to}
    end={exact}
    className={({ isActive }) =>
      cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 cursor-pointer",
        isActive
          ? "font-semibold"
          : "font-medium hover:opacity-80"
      )
    }
    style={({ isActive }) => ({
      backgroundColor: isActive ? '#EFF6FF' : 'transparent',
      color: isActive ? 'var(--color-primary)' : 'var(--color-text-muted)',
      fontFamily: 'var(--font-body)',
    })}
  >
    {({ isActive }) => (
      <>
        {React.cloneElement(icon, {
          size: 18,
          style: { color: isActive ? 'var(--color-primary)' : 'var(--color-text-muted)' },
        } as LucideProps & { style: React.CSSProperties })}
        {label}
      </>
    )}
  </NavLink>
);

const MobileNavLink: React.FC<NavLinkProps> = ({ to, icon, label, exact }) => (
  <NavLink
    to={to}
    end={exact}
    className="flex flex-col items-center gap-0.5 pt-1 pb-0.5 px-3 cursor-pointer transition-all duration-200"
  >
    {({ isActive }) => (
      <>
        {React.cloneElement(icon, {
          size: 22,
          style: { color: isActive ? 'var(--color-primary)' : '#94A3B8' },
        } as LucideProps & { style: React.CSSProperties })}
        <span
          className="text-xs font-medium"
          style={{
            color: isActive ? 'var(--color-primary)' : '#94A3B8',
            fontFamily: 'var(--font-body)',
          }}
        >
          {label}
        </span>
        {isActive && (
          <div
            className="w-1 h-1 rounded-full mt-0.5"
            style={{ backgroundColor: 'var(--color-primary)' }}
          />
        )}
      </>
    )}
  </NavLink>
);

export default Layout;
