import React from 'react';
import { AIInsight } from '../../types/analysis';
import { CitationList } from './CitationLink';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface InsightsPanelProps {
  insights: AIInsight[];
  onCitationClick?: (citation: any) => void;
  className?: string;
}

export const InsightsPanel: React.FC<InsightsPanelProps> = ({
  insights,
  onCitationClick,
  className = ''
}) => {
  if (!insights || insights.length === 0) {
    return (
      <Card className={className}>
        <CardContent>
          <div className="text-center py-12 text-gray-500">
            No AI insights available
          </div>
        </CardContent>
      </Card>
    );
  }

  const getSeverityBadge = (severity?: 'low' | 'medium' | 'high') => {
    if (!severity) return null;

    const variants: Record<string, 'success' | 'warning' | 'danger'> = {
      low: 'success',
      medium: 'warning',
      high: 'danger'
    };

    return (
      <Badge variant={variants[severity]} size="sm">
        {severity.toUpperCase()}
      </Badge>
    );
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'risk_assessment':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        );
      case 'liquidity_position':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
      case 'financial_health':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
      case 'recommendations':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'risk_assessment':
        return 'text-red-600 bg-red-50';
      case 'liquidity_position':
        return 'text-blue-600 bg-blue-50';
      case 'financial_health':
        return 'text-green-600 bg-green-50';
      case 'recommendations':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatCategoryTitle = (category: string) => {
    return category
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>AI-Powered Insights</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {insights.map((insight, index) => (
            <div
              key={`${insight.category}-${index}`}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${getCategoryColor(insight.category)}`}>
                    {getCategoryIcon(insight.category)}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">{insight.title}</h4>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {formatCategoryTitle(insight.category)}
                    </p>
                  </div>
                </div>
                {insight.severity && getSeverityBadge(insight.severity)}
              </div>

              {/* Content */}
              <div className="mb-3">
                <p className="text-gray-700 leading-relaxed">{insight.content}</p>
              </div>

              {/* Supporting Metrics */}
              {insight.supporting_metrics && insight.supporting_metrics.length > 0 && (
                <div className="mb-3">
                  <h5 className="text-sm font-medium text-gray-600 mb-2">Key Metrics:</h5>
                  <div className="flex flex-wrap gap-2">
                    {insight.supporting_metrics.map((metric, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                      >
                        {metric}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Citations */}
              {insight.citations && insight.citations.length > 0 && (
                <div className="pt-3 border-t border-gray-200">
                  <h5 className="text-sm font-medium text-gray-600 mb-2">Sources:</h5>
                  <CitationList citations={insight.citations} onClick={onCitationClick} />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Summary Footer */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center text-sm text-gray-600">
            <svg
              className="w-4 h-4 mr-2 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            These insights are AI-generated based on financial ratios and document analysis.
            Always verify critical decisions with professional financial advisors.
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
