/**
 * Main Layout Component
 * Provides the overall structure with sidebar navigation, header, and content area
 */

import { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  FolderIcon,
  Cog6ToothIcon,
  Bars3Icon,
  XMarkIcon,
  DocumentMagnifyingGlassIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { GlobalSearch, useGlobalSearch } from '../components/search/GlobalSearch';


interface NavItem {
  name: string;
  href: string;
  icon: any;
  exact?: boolean;
  color: string;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: HomeIcon, exact: true, color: 'blue' },
  { name: 'Cases', href: '/cases', icon: FolderIcon, color: 'slate' },
  { name: 'Analysis', href: '/analysis', icon: DocumentMagnifyingGlassIcon, color: 'teal' },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon, color: 'gray' },
];

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const search = useGlobalSearch();

  const isActiveRoute = (item: NavItem) => {
    if (item.exact) {
      return location.pathname === item.href;
    }
    return location.pathname.startsWith(item.href);
  };

  const getColorClasses = (color: string, isActive: boolean) => {
    const colors: Record<string, { active: string; inactive: string; icon: string }> = {
      blue: {
        active: 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 border-l-4 border-blue-600',
        inactive: 'text-gray-700 hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-blue-100/50',
        icon: isActive ? 'text-blue-600' : 'text-gray-500'
      },
      slate: {
        active: 'bg-gradient-to-r from-slate-100 to-slate-200 text-slate-800 border-l-4 border-slate-700',
        inactive: 'text-gray-700 hover:bg-gradient-to-r hover:from-slate-50/50 hover:to-slate-100/50',
        icon: isActive ? 'text-slate-700' : 'text-gray-500'
      },
      teal: {
        active: 'bg-gradient-to-r from-teal-50 to-teal-100 text-teal-800 border-l-4 border-teal-600',
        inactive: 'text-gray-700 hover:bg-gradient-to-r hover:from-teal-50/50 hover:to-teal-100/50',
        icon: isActive ? 'text-teal-600' : 'text-gray-500'
      },
      gray: {
        active: 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 border-l-4 border-gray-600',
        inactive: 'text-gray-700 hover:bg-gradient-to-r hover:from-gray-50/50 hover:to-gray-100/50',
        icon: isActive ? 'text-gray-600' : 'text-gray-500'
      },
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-gradient-to-b from-white via-gray-50/50 to-gray-100/50 border-r border-gray-200/60 shadow-xl transform transition-transform duration-300 ease-in-out lg:hidden',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200/60 bg-white/80 backdrop-blur-sm">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="relative p-2 rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 shadow-lg group-hover:shadow-xl group-hover:shadow-slate-400/50 transition-all duration-200 group-hover:scale-105 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-600/20 to-purple-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <DocumentMagnifyingGlassIcon className="w-6 h-6 text-white relative z-10" />
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">IIP</h1>
              <p className="text-xs text-gray-600 font-medium">Intelligence Platform</p>
            </div>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <XMarkIcon className="w-6 h-6 text-gray-500" />
          </button>
        </div>
        <nav className="px-4 py-4 space-y-2">
          {/* Navigation Items */}
          {navigation.map((item) => {
            const isActive = isActiveRoute(item);
            const colorClasses = getColorClasses(item.color, isActive);
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  'flex items-center px-4 py-3 text-sm font-semibold rounded-xl transition-all duration-200',
                  isActive ? colorClasses.active : colorClasses.inactive
                )}
              >
                <item.icon className={cn('w-5 h-5 mr-3', colorClasses.icon)} />
                {item.name}
              </Link>
            );
          })}

          {/* Divider */}
          <div className="pt-4 pb-2">
            <div className="h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
          </div>

          {/* Global Search Button - Mobile */}
          <button
            onClick={() => {
              search.open();
              setSidebarOpen(false);
            }}
            className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-600 bg-white hover:bg-gradient-to-r hover:from-slate-50 hover:to-gray-100 rounded-xl border-2 border-gray-200 hover:border-slate-300 transition-all duration-200 shadow-sm group"
          >
            <div className="flex items-center">
              <MagnifyingGlassIcon className="w-5 h-5 mr-3 text-slate-600 group-hover:text-slate-700" />
              <span className="text-gray-600 group-hover:text-slate-800">Search...</span>
            </div>
            <kbd className="inline-flex items-center gap-0.5 px-2 py-1 text-xs font-mono font-semibold text-slate-600 bg-gray-100 rounded border border-gray-300">
              <span>⌘</span>
              <span>K</span>
            </kbd>
          </button>
        </nav>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-gradient-to-b from-white via-gray-50/50 to-gray-100/50 border-r border-gray-200/60 shadow-lg">
          {/* Logo */}
          <div className="flex items-center h-16 px-6 border-b border-gray-200/60 bg-white/80 backdrop-blur-sm">
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="relative p-2 rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 shadow-lg group-hover:shadow-xl group-hover:shadow-slate-400/50 transition-all duration-200 group-hover:scale-105 overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-tr from-blue-600/20 to-purple-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <DocumentMagnifyingGlassIcon className="w-6 h-6 text-white relative z-10" />
              </div>
              <div>
                <h1 className="text-lg font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">IIP</h1>
                <p className="text-xs text-gray-600 font-medium">Intelligence Platform</p>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {/* Navigation Items */}
            {navigation.map((item) => {
              const isActive = isActiveRoute(item);
              const colorClasses = getColorClasses(item.color, isActive);
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center px-4 py-3 text-sm font-semibold rounded-xl transition-all duration-200 shadow-sm hover:shadow-md',
                    isActive ? colorClasses.active : colorClasses.inactive
                  )}
                >
                  <item.icon className={cn('w-5 h-5 mr-3', colorClasses.icon)} />
                  {item.name}
                </Link>
              );
            })}

            {/* Divider */}
            <div className="pt-4 pb-2">
              <div className="h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
            </div>

            {/* Global Search Button */}
            <button
              onClick={search.open}
              className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-600 bg-white hover:bg-gradient-to-r hover:from-slate-50 hover:to-gray-100 rounded-xl border-2 border-gray-200 hover:border-slate-300 transition-all duration-200 shadow-sm hover:shadow-md group"
            >
              <div className="flex items-center">
                <MagnifyingGlassIcon className="w-5 h-5 mr-3 text-slate-600 group-hover:text-slate-700" />
                <span className="text-gray-600 group-hover:text-slate-800">Search...</span>
              </div>
              <kbd className="hidden lg:inline-flex items-center gap-0.5 px-2 py-1 text-xs font-mono font-semibold text-slate-600 bg-gray-100 rounded border border-gray-300">
                <span>⌘</span>
                <span>K</span>
              </kbd>
            </button>
          </nav>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200/60 bg-white/50 backdrop-blur-sm">
            <div className="text-xs text-gray-600">
              <p className="font-semibold">Version 1.0.0</p>
              <p className="mt-1 font-medium">Investigation Intelligence Platform</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <div className="sticky top-0 z-40 flex items-center justify-between h-16 px-4 bg-white/90 backdrop-blur-sm border-b border-gray-200/60 shadow-sm lg:hidden">
          <div className="flex items-center">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 mr-2 rounded-lg hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all"
            >
              <Bars3Icon className="w-6 h-6 text-gray-600" />
            </button>
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="p-1.5 rounded-lg bg-gradient-to-br from-slate-700 to-slate-900 shadow-md group-hover:shadow-lg transition-all duration-200">
                <DocumentMagnifyingGlassIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">IIP</span>
            </Link>
          </div>
          <button
            onClick={search.open}
            className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 transition-all"
          >
            <MagnifyingGlassIcon className="w-5 h-5 text-slate-700" />
          </button>
        </div>

        {/* Page content */}
        <main className="min-h-screen">
          <Outlet />
        </main>
      </div>

      {/* Global Search Modal */}
      <GlobalSearch isOpen={search.isOpen} onClose={search.close} />
    </div>
  );
}
