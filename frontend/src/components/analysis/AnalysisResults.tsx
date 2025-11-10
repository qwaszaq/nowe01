import React, { useState } from 'react';
import { AnalysisResult } from '../../types/analysis';
import { QualityScoreCard } from './QualityScoreCard';
import { MetricsTable } from './MetricsTable';
import { MetricsCharts } from './MetricsCharts';
import { MetricCardGrid } from './MetricCard';
import { InsightsPanel } from './InsightsPanel';
import { ExportMenu } from './ExportMenu';

interface AnalysisResultsProps {
  data: AnalysisResult;
  onCitationClick?: (citation: any) => void;
  className?: string;
}

type ViewMode = 'grid' | 'table' | 'charts';

export const AnalysisResults: React.FC<AnalysisResultsProps> = ({
  data,
  onCitationClick,
  className = ''
}) => {
  const [metricsViewMode, setMetricsViewMode] = useState<ViewMode>('table');

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Export */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
          <p className="text-sm text-gray-600 mt-1">
            {data.cached ? (
              <span className="flex items-center">
                <svg
                  className="w-4 h-4 mr-1 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Cached results from{' '}
                {new Date(data.updated_at).toLocaleString()}
              </span>
            ) : (
              <span className="flex items-center">
                <svg
                  className="w-4 h-4 mr-1 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Generated {new Date(data.created_at).toLocaleString()}
              </span>
            )}
          </p>
        </div>
        <ExportMenu documentId={data.document_id} analysisType={data.analysis_type} />
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left Column - Quality Score and Metrics */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          {/* Quality Score */}
          <QualityScoreCard score={data.quality_score} />

          {/* Metrics View Toggle */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Financial Metrics ({data.metrics.length})
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={() => setMetricsViewMode('grid')}
                  className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                    metricsViewMode === 'grid'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  title="Grid view"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                    />
                  </svg>
                </button>
                <button
                  onClick={() => setMetricsViewMode('table')}
                  className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                    metricsViewMode === 'table'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  title="Table view"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                </button>
                <button
                  onClick={() => setMetricsViewMode('charts')}
                  className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                    metricsViewMode === 'charts'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  title="Charts view"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                </button>
              </div>
            </div>

            {/* Metrics Display */}
            {metricsViewMode === 'grid' && (
              <MetricCardGrid metrics={data.metrics} onCitationClick={onCitationClick} />
            )}
            {metricsViewMode === 'table' && (
              <MetricsTable metrics={data.metrics} onCitationClick={onCitationClick} />
            )}
            {metricsViewMode === 'charts' && (
              <MetricsCharts metrics={data.metrics} />
            )}
          </div>
        </div>

        {/* Right Column - Insights */}
        <div className="col-span-12 lg:col-span-4">
          <InsightsPanel insights={data.insights} onCitationClick={onCitationClick} />
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Metrics</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{data.metrics.length}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">AI Insights</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{data.insights.length}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <svg
                className="w-6 h-6 text-green-600"
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
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Analysis Type</p>
              <p className="text-2xl font-bold text-gray-900 mt-1 capitalize">
                {data.analysis_type}
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <svg
                className="w-6 h-6 text-purple-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
