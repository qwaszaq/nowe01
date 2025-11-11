/**
 * CasePagination Component
 * Pagination controls with page info and navigation
 */

import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface CasePaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export function CasePagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
}: CasePaginationProps) {
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const canGoPrevious = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  // Generate page numbers to show
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 7; // Maximum number of page buttons to show

    if (totalPages <= maxVisible) {
      // Show all pages
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show first page
      pages.push(1);

      if (currentPage <= 3) {
        // Near start
        for (let i = 2; i <= 4; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        // Near end
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        // In middle
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-gray-50 to-blue-50/30 border border-gray-200/60 rounded-xl px-4 py-4 flex items-center justify-between sm:px-6 mt-6 shadow-sm">
      {/* Mobile View */}
      <div className="flex-1 flex justify-between sm:hidden">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!canGoPrevious}
          className={`relative inline-flex items-center px-4 py-2 border text-sm font-semibold rounded-lg transition-all duration-200 ${
            canGoPrevious
              ? 'text-gray-700 bg-white hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 border-gray-300 hover:border-blue-300 shadow-sm'
              : 'text-gray-400 bg-gray-100 border-gray-200 cursor-not-allowed'
          }`}
        >
          Poprzednia
        </button>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!canGoNext}
          className={`ml-3 relative inline-flex items-center px-4 py-2 border text-sm font-semibold rounded-lg transition-all duration-200 ${
            canGoNext
              ? 'text-gray-700 bg-white hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 border-gray-300 hover:border-blue-300 shadow-sm'
              : 'text-gray-400 bg-gray-100 border-gray-200 cursor-not-allowed'
          }`}
        >
          Następna
        </button>
      </div>

      {/* Desktop View */}
      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-gray-700 font-medium">
            Wyświetlanie <span className="font-bold text-gray-900">{startItem}</span> do{' '}
            <span className="font-bold text-gray-900">{endItem}</span> z{' '}
            <span className="font-bold text-gray-900">{totalItems}</span> wyników
          </p>
        </div>
        <div>
          <nav className="relative z-0 inline-flex gap-2" aria-label="Pagination">
            {/* Previous Button */}
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!canGoPrevious}
              className={`relative inline-flex items-center px-3 py-2 rounded-lg border text-sm font-semibold transition-all duration-200 ${
                canGoPrevious
                  ? 'text-gray-700 bg-white hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 border-gray-300 hover:border-blue-300 shadow-sm'
                  : 'text-gray-300 bg-gray-100 border-gray-200 cursor-not-allowed'
              }`}
            >
              <ChevronLeftIcon className="h-5 w-5" aria-hidden="true" />
              <span className="ml-1">Poprzednia</span>
            </button>

            {/* Page Numbers */}
            {getPageNumbers().map((page, index) => {
              if (page === '...') {
                return (
                  <span
                    key={`ellipsis-${index}`}
                    className="relative inline-flex items-center px-2 text-sm font-bold text-gray-500"
                  >
                    ...
                  </span>
                );
              }

              const pageNumber = page as number;
              const isCurrentPage = pageNumber === currentPage;

              return (
                <button
                  key={pageNumber}
                  onClick={() => onPageChange(pageNumber)}
                  className={`relative inline-flex items-center px-4 py-2 border rounded-lg text-sm font-semibold transition-all duration-200 ${
                    isCurrentPage
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white border-transparent shadow-md transform scale-105 z-10'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:border-blue-300 shadow-sm'
                  }`}
                >
                  {pageNumber}
                </button>
              );
            })}

            {/* Next Button */}
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!canGoNext}
              className={`relative inline-flex items-center px-3 py-2 rounded-lg border text-sm font-semibold transition-all duration-200 ${
                canGoNext
                  ? 'text-gray-700 bg-white hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 border-gray-300 hover:border-blue-300 shadow-sm'
                  : 'text-gray-300 bg-gray-100 border-gray-200 cursor-not-allowed'
              }`}
            >
              <span className="mr-1">Następna</span>
              <ChevronRightIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          </nav>
        </div>
      </div>
    </div>
  );
}
