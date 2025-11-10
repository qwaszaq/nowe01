import React, { useState } from 'react';
import { FinancialMetric } from '../../types/analysis';
import { interpretRatio, getStatusColor, getStatusIcon } from '../../lib/metricInterpretation';
import { CitationList } from './CitationLink';
import { Card, CardContent } from '../ui/Card';

interface MetricCardProps {
  metric: FinancialMetric;
  onCitationClick?: (citation: any) => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({ metric, onCitationClick }) => {
  const [expanded, setExpanded] = useState(false);

  // Get interpretation if not provided
  const interpretation = metric.interpretation || interpretRatio(metric.name, metric.value);

  return (
    <Card padding="md" hover className="h-full">
      <CardContent>
        <div className="flex flex-col h-full">
          {/* Metric Name */}
          <div className="mb-2">
            <h4 className="text-sm font-medium text-gray-600">{metric.name}</h4>
          </div>

          {/* Value Display */}
          <div className="mb-3">
            <div className="text-3xl font-bold text-gray-900">
              {metric.formatted_value}
            </div>
          </div>

          {/* Status Badge */}
          <div className="mb-3">
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(
                interpretation.status
              )}`}
            >
              <span className="mr-1">{getStatusIcon(interpretation.status)}</span>
              {interpretation.status === 'good' && 'Good'}
              {interpretation.status === 'warning' && 'Warning'}
              {interpretation.status === 'poor' && 'Poor'}
            </span>
          </div>

          {/* Interpretation Text */}
          <div className="mb-3 flex-grow">
            <p className="text-sm text-gray-700">{interpretation.text}</p>
          </div>

          {/* Citations */}
          {metric.citations && metric.citations.length > 0 && (
            <div className="mb-3">
              <CitationList citations={metric.citations} onClick={onCitationClick} />
            </div>
          )}

          {/* Expand/Collapse for Details */}
          <div>
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              {expanded ? 'Show less' : 'Show details'}
            </button>

            {expanded && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <dl className="space-y-2 text-sm">
                  <div>
                    <dt className="font-medium text-gray-600">Category</dt>
                    <dd className="text-gray-900 capitalize">{metric.category}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-gray-600">Raw Value</dt>
                    <dd className="text-gray-900">{metric.value.toFixed(4)}</dd>
                  </div>
                  {metric.citations && metric.citations.length > 0 && (
                    <div>
                      <dt className="font-medium text-gray-600">Source Document</dt>
                      <dd className="text-gray-900">{metric.citations[0].document_name}</dd>
                    </div>
                  )}
                </dl>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

interface MetricCardGridProps {
  metrics: FinancialMetric[];
  onCitationClick?: (citation: any) => void;
}

export const MetricCardGrid: React.FC<MetricCardGridProps> = ({
  metrics,
  onCitationClick
}) => {
  if (!metrics || metrics.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No metrics available
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {metrics.map((metric, index) => (
        <MetricCard
          key={`${metric.name}-${index}`}
          metric={metric}
          onCitationClick={onCitationClick}
        />
      ))}
    </div>
  );
};
