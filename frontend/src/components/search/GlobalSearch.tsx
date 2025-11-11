/**
 * GlobalSearch Component
 * Global search bar with keyboard shortcut (Cmd+K / Ctrl+K)
 * Searches across cases and documents
 */

import { useState, useEffect, useCallback, Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, DocumentTextIcon, FolderIcon } from '@heroicons/react/24/outline';
import { Dialog, Transition } from '@headlessui/react';
import { useCases } from '../../hooks/useCases';
import type { Case } from '../../types/api';

interface SearchResult {
  id: string;
  type: 'case' | 'document';
  title: string;
  subtitle?: string;
  url: string;
}

interface GlobalSearchProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GlobalSearch({ isOpen, onClose }: GlobalSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const navigate = useNavigate();

  // Fetch cases for search
  const { data: casesData } = useCases({ page: 1, page_size: 100 });

  // Search function
  const performSearch = useCallback((searchQuery: string) => {
    if (!searchQuery.trim() || !casesData?.cases) {
      setResults([]);
      return;
    }

    const lowercaseQuery = searchQuery.toLowerCase();
    const caseResults: SearchResult[] = casesData.cases
      .filter((caseItem: Case) =>
        caseItem.name.toLowerCase().includes(lowercaseQuery) ||
        caseItem.description?.toLowerCase().includes(lowercaseQuery)
      )
      .slice(0, 5)
      .map((caseItem: Case) => ({
        id: caseItem.id,
        type: 'case' as const,
        title: caseItem.name,
        subtitle: caseItem.description || undefined,
        url: `/cases/${caseItem.id}`,
      }));

    setResults(caseResults);
  }, [casesData]);

  // Handle search input change
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      performSearch(query);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query, performSearch]);

  // Handle result selection
  const handleSelect = (result: SearchResult) => {
    navigate(result.url);
    onClose();
    setQuery('');
  };

  // Reset on close
  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      setResults([]);
    }
  }, [isOpen]);

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-start justify-center p-4 pt-[20vh]">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white shadow-2xl transition-all border border-gray-200/60">
                {/* Search Input */}
                <div className="relative border-b border-gray-200/60 bg-gradient-to-r from-slate-50 to-gray-100">
                  <MagnifyingGlassIcon className="absolute left-5 top-1/2 -translate-y-1/2 h-6 w-6 text-slate-600" />
                  <input
                    type="text"
                    className="w-full bg-transparent py-5 pl-14 pr-5 text-lg font-medium text-gray-900 placeholder-gray-500 outline-none"
                    placeholder="Search cases and documents..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    autoFocus
                  />
                  <div className="absolute right-5 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs font-mono font-semibold text-slate-600 bg-white rounded border border-gray-300 shadow-sm">
                      <span className="text-base">ESC</span>
                    </kbd>
                  </div>
                </div>

                {/* Search Results */}
                {query.trim() && (
                  <div className="max-h-[60vh] overflow-y-auto p-2">
                    {results.length > 0 ? (
                      <div className="space-y-1">
                        {results.map((result) => (
                          <button
                            key={`${result.type}-${result.id}`}
                            onClick={() => handleSelect(result)}
                            className="w-full text-left px-4 py-3 rounded-xl hover:bg-gradient-to-r hover:from-slate-50 hover:to-gray-100 transition-all duration-200 group"
                          >
                            <div className="flex items-start gap-3">
                              <div className={`flex-shrink-0 p-2 rounded-lg ${
                                result.type === 'case'
                                  ? 'bg-blue-100 text-blue-700 group-hover:bg-blue-200'
                                  : 'bg-emerald-100 text-emerald-700 group-hover:bg-emerald-200'
                              } transition-colors`}>
                                {result.type === 'case' ? (
                                  <FolderIcon className="h-5 w-5" />
                                ) : (
                                  <DocumentTextIcon className="h-5 w-5" />
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className={`text-xs font-mono font-semibold tracking-wider uppercase ${
                                    result.type === 'case' ? 'text-blue-700' : 'text-emerald-700'
                                  }`}>
                                    {result.type}
                                  </span>
                                </div>
                                <p className="text-sm font-semibold text-gray-900 truncate">
                                  {result.title}
                                </p>
                                {result.subtitle && (
                                  <p className="text-xs text-gray-600 truncate mt-1 leading-relaxed">
                                    {result.subtitle}
                                  </p>
                                )}
                              </div>
                              <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                                <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                              </div>
                            </div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="py-12 text-center">
                        <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <p className="mt-4 text-sm font-medium text-gray-900">No results found</p>
                        <p className="mt-1 text-xs text-gray-600">
                          Try searching with different keywords
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Empty State */}
                {!query.trim() && (
                  <div className="py-12 text-center px-6">
                    <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-slate-400" />
                    <p className="mt-4 text-sm font-medium text-gray-900">Search across your cases</p>
                    <p className="mt-1 text-xs text-gray-600 leading-relaxed">
                      Find cases, documents, and analysis results
                    </p>
                    <div className="mt-6 flex items-center justify-center gap-4 text-xs text-gray-500">
                      <div className="flex items-center gap-2">
                        <FolderIcon className="h-4 w-4 text-blue-600" />
                        <span className="font-mono font-semibold tracking-wider">CASES</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <DocumentTextIcon className="h-4 w-4 text-emerald-600" />
                        <span className="font-mono font-semibold tracking-wider">DOCUMENTS</span>
                      </div>
                    </div>
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

export function useGlobalSearch() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setIsOpen((open) => !open);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen((open) => !open),
  };
}
