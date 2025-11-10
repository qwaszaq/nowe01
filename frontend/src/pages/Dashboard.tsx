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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Investigation Cases</h1>
              <p className="mt-1 text-sm text-gray-600">
                Manage and analyze your investigation cases
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Create New Case
            </button>
          </div>
        </div>
      </div>

      {/* Dashboard Stats */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {statsLoading ? (
          <LoadingSkeleton variant="stats" count={4} className="mb-8" />
        ) : dashboardStats ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-gray-600">Total Cases</p>
                <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                  <FolderIcon className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-gray-900">{dashboardStats.totalCases}</p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-gray-600">Active Cases</p>
                <div className="p-2 rounded-lg bg-green-50 text-green-600">
                  <FolderIcon className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-gray-900">{dashboardStats.activeCases}</p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-gray-600">Completed Cases</p>
                <div className="p-2 rounded-lg bg-purple-50 text-purple-600">
                  <FolderIcon className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-gray-900">{dashboardStats.completedCases}</p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-gray-600">Archived Cases</p>
                <div className="p-2 rounded-lg bg-yellow-50 text-yellow-600">
                  <FolderIcon className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {dashboardStats.archivedCases}
              </p>
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
