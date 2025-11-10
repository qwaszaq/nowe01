import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { useAnalysisHistory } from '../../hooks/useAnalysis';
import { AnalysisResult, ANALYSIS_TYPE_LABELS } from '../../types/analysis';
import { interpretQualityScore } from '../../lib/metricInterpretation';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { LoadingOverlay } from '../ui/Spinner';

interface AnalysisHistoryProps {
  documentId: string;
  onViewAnalysis?: (analysis: AnalysisResult) => void;
  onCompareAnalysis?: (analysis1: AnalysisResult, analysis2: AnalysisResult) => void;
  className?: string;
}

export const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({
  documentId,
  onViewAnalysis,
  onCompareAnalysis,
  className = ''
}) => {
  const { data: history, isLoading, isError } = useAnalysisHistory(documentId);
  const [selectedForCompare, setSelectedForCompare] = React.useState<AnalysisResult | null>(null);

  const handleCompareClick = (analysis: AnalysisResult) => {
    if (selectedForCompare) {
      if (onCompareAnalysis) {
        onCompareAnalysis(selectedForCompare, analysis);
      }
      setSelectedForCompare(null);
    } else {
      setSelectedForCompare(analysis);
    }
  };

  const getQualityScoreBadge = (score: number) => {
    const interpretation = interpretQualityScore(score);
    const variants: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
      green: 'success',
      blue: 'info',
      yellow: 'warning',
      red: 'danger'
    };

    return (
      <Badge variant={variants[interpretation.color]} size="sm">
        {score}%
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <LoadingOverlay message="Loading analysis history..." />
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className={className}>
        <CardContent>
          <div className="text-center py-8 text-red-600">
            Failed to load analysis history
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!history || history.length === 0) {
    return (
      <Card className={className}>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            No analysis history available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Analysis History</CardTitle>
          {selectedForCompare && (
            <button
              onClick={() => setSelectedForCompare(null)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Cancel comparison
            </button>
          )}
        </div>
      </CardHeader>
      <CardContent padding="none">
        <div className="divide-y divide-gray-200">
          {history.map((analysis) => {
            const isSelected = selectedForCompare?.id === analysis.id;
            const createdDate = new Date(analysis.created_at);

            return (
              <div
                key={analysis.id}
                className={`p-4 hover:bg-gray-50 transition-colors ${
                  isSelected ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  {/* Left side - Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-semibold text-gray-900">
                        {ANALYSIS_TYPE_LABELS[analysis.analysis_type]}
                      </h4>
                      {getQualityScoreBadge(analysis.quality_score)}
                      {analysis.cached && (
                        <Badge variant="default" size="sm">
                          Cached
                        </Badge>
                      )}
                    </div>

                    <div className="text-sm text-gray-600 space-y-1">
                      <div className="flex items-center">
                        <svg
                          className="w-4 h-4 mr-2"
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
                        <span>
                          {formatDistanceToNow(createdDate, { addSuffix: true })}
                        </span>
                      </div>

                      <div className="flex items-center">
                        <svg
                          className="w-4 h-4 mr-2"
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
                        <span>{analysis.metrics.length} metrics analyzed</span>
                      </div>

                      {analysis.insights && analysis.insights.length > 0 && (
                        <div className="flex items-center">
                          <svg
                            className="w-4 h-4 mr-2"
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
                          <span>{analysis.insights.length} AI insights</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right side - Actions */}
                  <div className="flex gap-2 ml-4">
                    {onViewAnalysis && (
                      <button
                        onClick={() => onViewAnalysis(analysis)}
                        className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      >
                        View
                      </button>
                    )}

                    {onCompareAnalysis && (
                      <button
                        onClick={() => handleCompareClick(analysis)}
                        className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                          isSelected
                            ? 'bg-blue-600 text-white'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        {isSelected ? 'Selected' : selectedForCompare ? 'Compare' : 'Select'}
                      </button>
                    )}
                  </div>
                </div>

                {/* Quality Score Trend */}
                {history.length > 1 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Quality Score Trend</span>
                      <div className="flex items-center gap-4">
                        {history.map((h, idx) => {
                          if (idx === 0) return null;
                          const prev = history[idx - 1];
                          const diff = h.quality_score - prev.quality_score;
                          return (
                            <div key={h.id} className="flex items-center">
                              {diff > 0 ? (
                                <svg
                                  className="w-4 h-4 text-green-600 mr-1"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M5 10l7-7m0 0l7 7m-7-7v18"
                                  />
                                </svg>
                              ) : diff < 0 ? (
                                <svg
                                  className="w-4 h-4 text-red-600 mr-1"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M19 14l-7 7m0 0l-7-7m7 7V3"
                                  />
                                </svg>
                              ) : null}
                              <span className={diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : ''}>
                                {diff > 0 ? '+' : ''}{diff.toFixed(1)}%
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};
