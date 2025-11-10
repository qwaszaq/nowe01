import React, { useState } from 'react';
import { SemanticSearchResult } from '../../types/analysis';
import { Card, CardContent } from '../ui/Card';

interface SearchResultsProps {
  results: SemanticSearchResult[];
  query: string;
  onViewInContext?: (result: SemanticSearchResult) => void;
  className?: string;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  query,
  onViewInContext,
  className = ''
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState<'relevance' | 'page'>('relevance');
  const resultsPerPage = 10;

  // Highlight query terms in text
  const highlightText = (text: string, queryText: string) => {
    if (!queryText) return text;

    // Extract words from query (at least 3 chars)
    const words = queryText.toLowerCase().split(/\s+/).filter(w => w.length >= 3);
    if (words.length === 0) return text;

    // Escape special regex characters and create pattern
    const escapedWords = words.map(word =>
      word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    );

    // Create regex that matches any of the words
    const pattern = new RegExp(`(${escapedWords.join('|')})`, 'gi');

    // Replace matches with highlighted version
    return text.replace(pattern, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>');
  };

  // Sort results
  const sortedResults = [...results].sort((a, b) => {
    if (sortBy === 'relevance') {
      return b.score - a.score;
    } else {
      return a.page_num - b.page_num;
    }
  });

  // Paginate results
  const totalPages = Math.ceil(sortedResults.length / resultsPerPage);
  const startIndex = (currentPage - 1) * resultsPerPage;
  const paginatedResults = sortedResults.slice(startIndex, startIndex + resultsPerPage);

  if (!results || results.length === 0) {
    return (
      <Card className={className}>
        <CardContent>
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search query or using different terms.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Search Results ({results.length})
          </h3>
          <p className="text-sm text-gray-600">
            Showing {startIndex + 1}-{Math.min(startIndex + resultsPerPage, results.length)} of{' '}
            {results.length} results
          </p>
        </div>

        {/* Sort Options */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'relevance' | 'page')}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="relevance">Relevance</option>
            <option value="page">Page Number</option>
          </select>
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-4">
        {paginatedResults.map((result, index) => (
          <Card key={`${result.document_id}-${result.page_num}-${index}`} hover>
            <CardContent>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Score and Page */}
                  <div className="flex items-center gap-3 mb-2">
                    <div className="flex items-center">
                      <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${result.score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-700">
                        {(result.score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      <span>Dokument {result.document_id.substring(0, 8)}...</span>
                      <span>•</span>
                      <span>Strona {result.page_num}</span>
                    </div>
                  </div>

                  {/* Text Excerpt */}
                  <div
                    className="text-gray-800 leading-relaxed mb-3"
                    dangerouslySetInnerHTML={{
                      __html: highlightText(
                        result.text.length > 300
                          ? result.text.substring(0, 300) + '...'
                          : result.text,
                        query
                      )
                    }}
                  />

                  {/* Context Information */}
                  {result.context && (result.context.before.length > 0 || result.context.after.length > 0) && (
                    <div className="text-xs text-gray-500 mb-2">
                      Kontekst: {result.context.before.length} fragmentów przed, {result.context.after.length} fragmentów po
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="ml-4">
                  <button
                    onClick={() => onViewInContext && onViewInContext(result)}
                    className="px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
                  >
                    View in context
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          <div className="flex items-center gap-1">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
              // Show first page, last page, current page, and pages around current
              const showPage =
                page === 1 ||
                page === totalPages ||
                (page >= currentPage - 1 && page <= currentPage + 1);

              if (!showPage) {
                // Show ellipsis
                if (page === currentPage - 2 || page === currentPage + 2) {
                  return (
                    <span key={page} className="px-2 text-gray-500">
                      ...
                    </span>
                  );
                }
                return null;
              }

              return (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`px-3 py-2 border rounded-md text-sm font-medium ${
                    currentPage === page
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
