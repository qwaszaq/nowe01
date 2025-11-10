import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAnalysis, useRunAnalysis } from '../hooks/useAnalysis';
import { AnalysisType } from '../types/analysis';
import { AnalysisTypeSelector } from '../components/analysis/AnalysisTypeSelector';
import { AnalysisResults } from '../components/analysis/AnalysisResults';
import { SemanticSearch } from '../components/analysis/SemanticSearch';
import { AnalysisHistory } from '../components/analysis/AnalysisHistory';
import { Button } from '../components/ui/Button';
import { LoadingOverlay } from '../components/ui/Spinner';
import { formatDistanceToNow } from 'date-fns';

export const AnalysisPage: React.FC = () => {
  const { caseId, documentId } = useParams<{ caseId: string; documentId: string }>();
  const navigate = useNavigate();
  const [analysisType, setAnalysisType] = useState<AnalysisType>('comprehensive');
  const [showHistory, setShowHistory] = useState(false);

  const {
    data: analysisData,
    isLoading,
    isError,
    error
  } = useAnalysis(documentId || null, analysisType);

  const runAnalysisMutation = useRunAnalysis();

  const handleRunAnalysis = async (forceRefresh = false) => {
    if (!documentId) return;

    try {
      await runAnalysisMutation.mutateAsync({
        documentId,
        analysisType,
        forceRefresh
      });
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };

  const handleCitationClick = (citation: any) => {
    // Navigate to document viewer at specific page
    window.open(`/documents/${citation.document_id}?page=${citation.page}`, '_blank');
  };

  if (!documentId || !caseId) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Invalid document or case ID</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <button
                onClick={() => navigate(`/cases/${caseId}/documents/${documentId}`)}
                className="flex items-center text-gray-600 hover:text-gray-900 mb-2"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
                Back to Document
              </button>
              <h1 className="text-3xl font-bold text-gray-900">Financial Analysis</h1>
              <p className="text-gray-600 mt-1">
                Document ID: {documentId}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                {showHistory ? 'Hide History' : 'View History'}
              </button>
            </div>
          </div>

          {/* Analysis Type Selector */}
          <AnalysisTypeSelector value={analysisType} onChange={setAnalysisType} />
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Run Analysis Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {analysisData?.cached ? 'Cached Analysis Available' : 'Run New Analysis'}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {analysisData?.cached ? (
                  <>
                    Last updated{' '}
                    {formatDistanceToNow(new Date(analysisData.updated_at), { addSuffix: true })}
                  </>
                ) : (
                  'Generate a comprehensive financial analysis for this document'
                )}
              </p>
            </div>

            <div className="flex items-center gap-3">
              {analysisData?.cached && (
                <Button
                  onClick={() => handleRunAnalysis(true)}
                  isLoading={runAnalysisMutation.isPending}
                  variant="outline"
                >
                  Refresh Analysis
                </Button>
              )}
              <Button
                onClick={() => handleRunAnalysis(false)}
                isLoading={runAnalysisMutation.isPending}
                variant="primary"
              >
                {runAnalysisMutation.isPending ? 'Analyzing...' : 'Run Analysis'}
              </Button>
            </div>
          </div>

          {/* Progress Bar */}
          {runAnalysisMutation.isPending && (
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Processing financial data and generating insights...
              </p>
            </div>
          )}

          {/* Error State */}
          {runAnalysisMutation.isError && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
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
                  <h4 className="text-sm font-medium text-red-800">Analysis Failed</h4>
                  <p className="text-sm text-red-700 mt-1">
                    {runAnalysisMutation.error instanceof Error
                      ? runAnalysisMutation.error.message
                      : 'An error occurred while running the analysis. Please try again.'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* History Panel */}
        {showHistory && (
          <div className="mb-6">
            <AnalysisHistory
              documentId={documentId}
              onViewAnalysis={(analysis) => {
                setAnalysisType(analysis.analysis_type);
                setShowHistory(false);
              }}
            />
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white rounded-lg border border-gray-200">
            <LoadingOverlay message="Loading analysis results..." />
          </div>
        )}

        {/* Error State */}
        {isError && !isLoading && (
          <div className="bg-white rounded-lg border border-gray-200 p-8">
            <div className="text-center">
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
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No Analysis Available</h3>
              <p className="mt-1 text-sm text-gray-500">
                {error instanceof Error ? error.message : 'Run an analysis to see results here.'}
              </p>
              <div className="mt-6">
                <Button onClick={() => handleRunAnalysis(false)}>
                  Run {analysisType} Analysis
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Analysis Results */}
        {analysisData && !isLoading && (
          <AnalysisResults data={analysisData} onCitationClick={handleCitationClick} />
        )}

        {/* Semantic Search */}
        {caseId && (
          <div className="mt-8">
            <SemanticSearch caseId={caseId} />
          </div>
        )}
      </div>
    </div>
  );
};
