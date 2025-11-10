import React, { useState } from 'react';
import { useSemanticSearch, EXAMPLE_QUERIES } from '../../hooks/useSemanticSearch';
import { SearchResults } from './SearchResults';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';

interface SemanticSearchProps {
  caseId: string;
  className?: string;
}

export const SemanticSearch: React.FC<SemanticSearchProps> = ({ caseId, className = '' }) => {
  const [query, setQuery] = useState('');
  const semanticSearch = useSemanticSearch();

  const handleSearch = async () => {
    if (!query.trim()) return;

    try {
      await semanticSearch.mutateAsync({
        caseId,
        query: query.trim(),
        limit: 20,
        minScore: 0.3
      });
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleExampleClick = (exampleQuery: string) => {
    setQuery(exampleQuery);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <CardTitle>Wyszukiwanie Semantyczne</CardTitle>
          <p className="text-sm text-gray-600 mt-1">
            Zadawaj pytania o dokumenty finansowe używając języka naturalnego
          </p>
        </CardHeader>
        <CardContent>
          {/* Search Input */}
          <div className="mb-4">
            <div className="flex gap-2">
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Zadaj pytanie o dokumenty..."
                leftIcon={
                  <svg
                    className="w-5 h-5 text-gray-400"
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
                }
                className="flex-1"
              />
              <Button
                onClick={handleSearch}
                isLoading={semanticSearch.isPending}
                disabled={!query.trim() || semanticSearch.isPending}
              >
                Szukaj
              </Button>
            </div>
          </div>

          {/* Example Queries */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Przykładowe pytania:</h4>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUERIES.map((example, index) => (
                <button
                  key={index}
                  onClick={() => handleExampleClick(example)}
                  className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded-full transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>

          {/* Loading State */}
          {semanticSearch.isPending && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <svg
                  className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                <p className="text-gray-600">Przeszukiwanie dokumentów...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {semanticSearch.isError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <div className="flex items-center">
                <svg
                  className="w-5 h-5 text-red-600 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div>
                  <h4 className="text-sm font-medium text-red-800">Wyszukiwanie nie powiodło się</h4>
                  <p className="text-sm text-red-700 mt-1">
                    {semanticSearch.error instanceof Error
                      ? semanticSearch.error.message
                      : 'Wystąpił błąd podczas wyszukiwania. Spróbuj ponownie.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          {semanticSearch.isSuccess && semanticSearch.data && (
            <div className="mt-6">
              <SearchResults
                results={semanticSearch.data}
                query={query}
                onViewInContext={(result) => {
                  // Open document viewer at specific page
                  window.open(
                    `/cases/${caseId}/documents/${result.document_id}?page=${result.page_num}`,
                    '_blank'
                  );
                }}
              />
            </div>
          )}

          {/* Initial State */}
          {!semanticSearch.data && !semanticSearch.isPending && !semanticSearch.isError && (
            <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
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
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                Inteligentne wyszukiwanie dokumentów
              </h3>
              <p className="mt-1 text-sm text-gray-500 max-w-md mx-auto">
                Używaj języka naturalnego do przeszukiwania wszystkich dokumentów sprawy. Nasza AI rozumie kontekst
                i znajduje istotne informacje nawet gdy dokładne słowa kluczowe się nie zgadzają.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
