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
      <div className="mb-6 p-6 bg-gradient-to-r from-slate-50 to-gray-100 rounded-xl border border-slate-200/50 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">
              Wyniki wyszukiwania ({results.length})
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Wyświetlanie {startIndex + 1}-{Math.min(startIndex + resultsPerPage, results.length)} z{' '}
              {results.length} wyników
            </p>
          </div>

          {/* Sort Options */}
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Sortuj:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'relevance' | 'page')}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm hover:border-blue-400 transition-colors"
            >
              <option value="relevance">Trafność</option>
              <option value="page">Numer strony</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-5">
        {paginatedResults.map((result, index) => (
          <Card key={`${result.document_id}-${result.page_num}-${index}`} hover>
            <CardContent>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  {/* Score and Page */}
                  <div className="flex items-center gap-4 mb-3">
                    <div className="flex items-center bg-gradient-to-r from-blue-50 to-purple-50 px-3 py-1.5 rounded-full">
                      <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${result.score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        {(result.score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-600 bg-gray-50 px-3 py-1.5 rounded-full">
                      <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      <span className="font-medium">Dokument {result.document_id.substring(0, 8)}...</span>
                      <span className="text-gray-400">•</span>
                      <span className="font-medium">Strona {result.page_num}</span>
                    </div>
                  </div>

                  {/* Text Excerpt */}
                  <div
                    className="text-gray-700 leading-relaxed mb-3 text-base p-4 bg-gray-50/50 rounded-lg border-l-4 border-blue-400"
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
                    <div className="flex items-center gap-2 text-xs text-gray-500 bg-blue-50 px-3 py-1.5 rounded-full inline-flex">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      <span className="font-medium">
                        Kontekst: {result.context.before.length} fragmentów przed, {result.context.after.length} fragmentów po
                      </span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex-shrink-0">
                  <button
                    onClick={() => onViewInContext && onViewInContext(result)}
                    className="px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-slate-700 to-slate-900 hover:from-slate-800 hover:to-black rounded-lg shadow-md hover:shadow-lg transform transition-all duration-200 hover:scale-105"
                  >
                    Zobacz w kontekście
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            Poprzednia
          </button>

          <div className="flex items-center gap-2">
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
                    <span key={page} className="px-2 text-gray-500 font-bold">
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
                  className={`px-4 py-2 border rounded-lg text-sm font-semibold transition-all duration-200 ${
                    currentPage === page
                      ? 'bg-gradient-to-r from-slate-700 to-slate-900 text-white border-transparent shadow-md transform scale-105'
                      : 'border-gray-300 text-gray-700 hover:bg-gradient-to-r hover:from-slate-50 hover:to-slate-100 hover:border-slate-300'
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
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            Następna
          </button>
        </div>
      )}
    </div>
  );
};
