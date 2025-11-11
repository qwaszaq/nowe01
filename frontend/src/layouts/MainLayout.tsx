/**
 * Main Layout Component
 * Provides the overall structure with top navigation bar and content area
 */

import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  FolderIcon,
  Cog6ToothIcon,
  DocumentMagnifyingGlassIcon,
  MagnifyingGlassIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { GlobalSearch, useGlobalSearch } from '../components/search/GlobalSearch';

interface NavItem {
  name: string;
  href: string;
  icon: any;
  exact?: boolean;
}

const navigation: NavItem[] = [
  { name: 'Cases', href: '/', icon: FolderIcon, exact: true },
  { name: 'BI Analytics', href: '/analytics', icon: ChartBarIcon, exact: false },
];

export default function MainLayout() {
  const location = useLocation();
  const search = useGlobalSearch();
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isActiveRoute = (item: NavItem) => {
    if (item.exact) {
      return location.pathname === item.href;
    }
    return location.pathname.startsWith(item.href);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <nav className={`fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-blue-200 via-blue-300 to-blue-200 transition-all duration-300 ${
        scrolled ? 'shadow-2xl shadow-blue-900/20' : 'shadow-lg'
      }`}>
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-28">
            {/* Logo and Left Navigation */}
            <div className="flex items-center gap-6">
              {/* Logo */}
              <Link to="/" className="flex items-center group">
                <div className="relative transition-all duration-200 group-hover:scale-105">
                  <img
                    src="/assets/cba-logo.svg"
                    alt="CBA Logo"
                    className="w-24 h-24 object-contain drop-shadow-lg"
                  />
                </div>
              </Link>

              {/* Navigation - Left Aligned */}
              <div className="hidden md:flex items-center gap-2">
                {navigation.map((item) => {
                  const isActive = isActiveRoute(item);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={cn(
                        'flex items-center px-5 py-2 text-sm font-bold rounded-lg transition-all duration-200',
                        isActive
                          ? 'bg-white text-blue-900 border-2 border-blue-900 shadow-md'
                          : 'bg-transparent text-blue-900 hover:bg-white/30 border-2 border-blue-900/50 hover:border-blue-900'
                      )}
                    >
                      <Icon className="w-5 h-5 mr-2" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-3">
              {/* Search Button - More Prominent */}
              <button
                onClick={search.open}
                className="hidden sm:flex items-center px-4 py-2 text-sm font-medium text-blue-900 bg-white/40 hover:bg-white/60 rounded-lg transition-all border border-blue-900/30 hover:border-blue-900/50"
              >
                <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
                <span className="hidden lg:inline">Search</span>
                <kbd className="ml-2 px-1.5 py-0.5 text-xs font-mono bg-blue-900/20 rounded border border-blue-900/30 text-blue-900">⌘K</kbd>
              </button>

              {/* Mobile Search */}
              <button
                onClick={search.open}
                className="sm:hidden p-2 rounded-lg bg-white/40 hover:bg-white/60 transition-all border border-blue-900/30"
              >
                <MagnifyingGlassIcon className="w-5 h-5 text-blue-900" />
              </button>

              {/* Settings Icon with Text */}
              <Link
                to="/settings"
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/30 hover:bg-white/50 text-blue-900 transition-all border border-blue-900/30 hover:border-blue-900/50"
                title="Settings"
              >
                <Cog6ToothIcon className="w-5 h-5" />
                <span className="hidden lg:inline text-sm font-medium">Settings</span>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-lg">
        <div className="flex items-center justify-around px-2 py-2">
          {navigation.map((item) => {
            const isActive = isActiveRoute(item);
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex flex-col items-center px-4 py-2 text-xs font-semibold rounded-lg transition-all',
                  isActive
                    ? 'text-blue-900 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                )}
              >
                <Icon className={cn('w-6 h-6 mb-1', isActive ? 'text-blue-700' : 'text-gray-500')} />
                {item.name}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Main content area */}
      <main className="pt-28 pb-20 md:pb-0">
        <Outlet />
      </main>

      {/* Global Search Modal */}
      <GlobalSearch isOpen={search.isOpen} onClose={search.close} />
    </div>
  );
}
