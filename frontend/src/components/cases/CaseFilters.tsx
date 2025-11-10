/**
 * CaseFilters Component
 * Filter controls for case list (status, search)
 */

import { MagnifyingGlassIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { CaseStatus, type CaseFilters as CaseFiltersType } from '../../types';

interface CaseFiltersProps {
  filters: CaseFiltersType;
  onChange: (filters: CaseFiltersType) => void;
}

export function CaseFilters({ filters, onChange }: CaseFiltersProps) {
  const handleStatusChange = (status: string) => {
    onChange({
      ...filters,
      status: status === '' ? undefined : (status as CaseStatus),
      page: 1, // Reset to first page when filtering
    });
  };

  const handleSearchChange = (search: string) => {
    onChange({
      ...filters,
      search: search || undefined,
      page: 1, // Reset to first page when searching
    });
  };

  const activeFilterCount = [filters.status, filters.search].filter(Boolean).length;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
      <div className="flex flex-col md:flex-row gap-4">
        {/* Search Input */}
        <div className="flex-1">
          <label htmlFor="search" className="sr-only">
            Search cases
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              id="search"
              value={filters.search || ''}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Search by case name..."
            />
          </div>
        </div>

        {/* Status Filter */}
        <div className="md:w-64">
          <label htmlFor="status" className="sr-only">
            Filter by status
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
            </div>
            <select
              id="status"
              value={filters.status || ''}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="">All Statuses</option>
              <option value={CaseStatus.OPEN}>Open</option>
              <option value={CaseStatus.IN_PROGRESS}>In Progress</option>
              <option value={CaseStatus.UNDER_REVIEW}>Under Review</option>
              <option value={CaseStatus.COMPLETED}>Completed</option>
              <option value={CaseStatus.ARCHIVED}>Archived</option>
              <option value={CaseStatus.CLOSED}>Closed</option>
            </select>
          </div>
        </div>

        {/* Clear Filters */}
        {activeFilterCount > 0 && (
          <button
            onClick={() => onChange({ page: 1, page_size: filters.page_size })}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Clear Filters ({activeFilterCount})
          </button>
        )}
      </div>
    </div>
  );
}
