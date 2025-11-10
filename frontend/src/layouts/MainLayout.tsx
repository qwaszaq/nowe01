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
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

interface NavItem {
  name: string;
  href: string;
  icon: any;
  exact?: boolean;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: HomeIcon, exact: true },
  { name: 'Cases', href: '/cases', icon: FolderIcon },
  { name: 'Analysis', href: '/analysis', icon: DocumentMagnifyingGlassIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const isActiveRoute = (item: NavItem) => {
    if (item.exact) {
      return location.pathname === item.href;
    }
    return location.pathname.startsWith(item.href);
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
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out lg:hidden',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          <Link to="/" className="flex items-center space-x-2">
            <DocumentMagnifyingGlassIcon className="w-8 h-8 text-primary-600" />
            <span className="text-lg font-bold text-gray-900">IIP</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            <XMarkIcon className="w-6 h-6 text-gray-500" />
          </button>
        </div>
        <nav className="px-4 py-4 space-y-1">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              onClick={() => setSidebarOpen(false)}
              className={cn(
                'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                isActiveRoute(item)
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.name}
            </Link>
          ))}
        </nav>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200">
          {/* Logo */}
          <div className="flex items-center h-16 px-6 border-b border-gray-200">
            <Link to="/" className="flex items-center space-x-3">
              <DocumentMagnifyingGlassIcon className="w-8 h-8 text-primary-600" />
              <div>
                <h1 className="text-lg font-bold text-gray-900">IIP</h1>
                <p className="text-xs text-gray-500">Intelligence Platform</p>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                  isActiveRoute(item)
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-100'
                )}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            ))}
          </nav>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="text-xs text-gray-500">
              <p className="font-medium">Version 1.0.0</p>
              <p className="mt-1">Investigation Intelligence Platform</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <div className="sticky top-0 z-10 flex items-center h-16 px-4 bg-white border-b border-gray-200 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 mr-2 rounded-lg hover:bg-gray-100"
          >
            <Bars3Icon className="w-6 h-6 text-gray-500" />
          </button>
          <Link to="/" className="flex items-center space-x-2">
            <DocumentMagnifyingGlassIcon className="w-6 h-6 text-primary-600" />
            <span className="text-lg font-bold text-gray-900">IIP</span>
          </Link>
        </div>

        {/* Page content */}
        <main className="min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
