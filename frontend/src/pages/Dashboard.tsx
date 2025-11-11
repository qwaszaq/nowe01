/**
 * Dashboard Page
 * Main landing page showing cases overview and stats
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon, FolderIcon } from '@heroicons/react/24/outline';
import { useCases, useDashboardStats } from '../hooks/useCases';
import { CaseList } from '../components/cases/CaseList';
import { CaseFilters } from '../components/cases/CaseFilters';
import { CasePagination } from '../components/cases/CasePagination';
import { CreateCaseModal } from '../components/cases/CreateCaseModal';
import { DeleteCaseDialog } from '../components/cases/DeleteCaseDialog';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import type { CaseFilters as CaseFiltersType, Case } from '../types';

export default function Dashboard() {
  const navigate = useNavigate();

  // Filters and pagination
  const [filters, setFilters] = useState<CaseFiltersType>({
    page: 1,
    page_size: 12,
  });

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [caseToDelete, setCaseToDelete] = useState<Case | null>(null);

  // Fetch data
  const { data: casesData, isLoading, error, refetch } = useCases(filters);
  const { data: dashboardStats, isLoading: statsLoading } = useDashboardStats();

  const handlePageChange = (page: number) => {
    setFilters({ ...filters, page });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCreateSuccess = (caseId: string) => {
    navigate(`/cases/${caseId}`);
  };

  const handleDeleteSuccess = () => {
    refetch();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-gray-50 to-gray-100">
      {/* Header - Fixed */}
      <div className="fixed top-16 lg:top-0 left-0 lg:left-64 right-0 z-30 bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">
                Investigation Cases
              </h1>
              <p className="mt-2 text-sm text-gray-600">
                Manage and analyze your investigation cases with AI-powered insights
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-6 py-3 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-slate-700 to-slate-900 hover:from-slate-800 hover:to-black transform transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Utwórz nową sprawę
            </button>
          </div>
        </div>
      </div>

      {/* Dashboard Stats - Add top padding to account for fixed header */}
      <div className="pt-48 lg:pt-32 px-4 sm:px-6 lg:px-8 pb-8 max-w-full">
        {statsLoading ? (
          <LoadingSkeleton variant="stats" count={4} className="mb-8" />
        ) : dashboardStats ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="group relative bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-6 shadow-lg hover:shadow-xl transform transition-all duration-300 hover:scale-105 overflow-hidden border border-blue-200/50">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-100 to-blue-200 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-blue-700">Wszystkie sprawy</p>
                  <div className="p-3 rounded-xl bg-blue-200/50 backdrop-blur-sm">
                    <FolderIcon className="h-6 w-6 text-blue-600" />
                  </div>
                </div>
                <p className="text-4xl font-bold text-blue-900 mb-1">{dashboardStats.totalCases}</p>
                <div className="flex items-center text-blue-600 text-xs font-medium">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clipRule="evenodd" />
                  </svg>
                  Łącznie
                </div>
              </div>
            </div>

            <div className="group relative bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-2xl p-6 shadow-lg hover:shadow-xl transform transition-all duration-300 hover:scale-105 overflow-hidden border border-emerald-200/50">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-100 to-emerald-200 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-emerald-700">Aktywne sprawy</p>
                  <div className="p-3 rounded-xl bg-emerald-200/50 backdrop-blur-sm">
                    <FolderIcon className="h-6 w-6 text-emerald-600" />
                  </div>
                </div>
                <p className="text-4xl font-bold text-emerald-900 mb-1">{dashboardStats.activeCases}</p>
                <div className="flex items-center text-emerald-600 text-xs font-medium">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  W toku
                </div>
              </div>
            </div>

            <div className="group relative bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-2xl p-6 shadow-lg hover:shadow-xl transform transition-all duration-300 hover:scale-105 overflow-hidden border border-cyan-200/50">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-100 to-cyan-200 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-cyan-700">Zakończone</p>
                  <div className="p-3 rounded-xl bg-cyan-200/50 backdrop-blur-sm">
                    <FolderIcon className="h-6 w-6 text-cyan-600" />
                  </div>
                </div>
                <p className="text-4xl font-bold text-cyan-900 mb-1">{dashboardStats.completedCases}</p>
                <div className="flex items-center text-cyan-600 text-xs font-medium">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Zamknięte
                </div>
              </div>
            </div>

            <div className="group relative bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl p-6 shadow-lg hover:shadow-xl transform transition-all duration-300 hover:scale-105 overflow-hidden border border-slate-200/50">
              <div className="absolute inset-0 bg-gradient-to-br from-slate-100 to-slate-200 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-slate-700">Zarchiwizowane</p>
                  <div className="p-3 rounded-xl bg-slate-200/50 backdrop-blur-sm">
                    <FolderIcon className="h-6 w-6 text-slate-600" />
                  </div>
                </div>
                <p className="text-4xl font-bold text-slate-900 mb-1">{dashboardStats.archivedCases}</p>
                <div className="flex items-center text-slate-600 text-xs font-medium">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4z" />
                    <path fillRule="evenodd" d="M3 8h14v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8zm5 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                  Archiwum
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {/* Filters */}
        <CaseFilters filters={filters} onChange={setFilters} />

        {/* Cases List */}
        {isLoading ? (
          <LoadingSkeleton variant="card" count={6} />
        ) : error ? (
          <ErrorMessage error={error} onRetry={refetch} variant="page" />
        ) : casesData ? (
          <>
            <CaseList
              cases={casesData.cases || []}
              onEdit={(caseItem) => navigate(`/cases/${caseItem.id}`)}
              onDelete={(caseItem) => setCaseToDelete(caseItem)}
              onCreate={() => setShowCreateModal(true)}
            />

            {/* Pagination */}
            {casesData.total > 0 && (
              <CasePagination
                currentPage={casesData.page}
                totalPages={casesData.total_pages}
                totalItems={casesData.total}
                pageSize={casesData.page_size}
                onPageChange={handlePageChange}
              />
            )}
          </>
        ) : null}
      </div>

      {/* Create Case Modal */}
      <CreateCaseModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleCreateSuccess}
      />

      {/* Delete Case Dialog */}
      <DeleteCaseDialog
        case={caseToDelete}
        isOpen={!!caseToDelete}
        onClose={() => setCaseToDelete(null)}
        onSuccess={handleDeleteSuccess}
      />
    </div>
  );
}
