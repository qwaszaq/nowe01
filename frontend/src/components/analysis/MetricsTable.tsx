import React, { useState, useMemo } from 'react';
import { FinancialMetric } from '../../types/analysis';
import { interpretRatio, getStatusColor, getStatusIcon } from '../../lib/metricInterpretation';
import { CitationList } from './CitationLink';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';

interface MetricsTableProps {
  metrics: FinancialMetric[];
  onCitationClick?: (citation: any) => void;
  className?: string;
}

type SortField = 'name' | 'value' | 'status';
type SortDirection = 'asc' | 'desc';

export const MetricsTable: React.FC<MetricsTableProps> = ({
  metrics,
  onCitationClick,
  className = ''
}) => {
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Group metrics by category
  const groupedMetrics = useMemo(() => {
    const groups: Record<string, FinancialMetric[]> = {
      liquidity: [],
      profitability: [],
      leverage: []
    };

    metrics.forEach((metric) => {
      if (groups[metric.category]) {
        groups[metric.category].push(metric);
      }
    });

    return groups;
  }, [metrics]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortMetrics = (metricsToSort: FinancialMetric[]) => {
    return [...metricsToSort].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'value':
          aValue = a.value;
          bValue = b.value;
          break;
        case 'status':
          const aInterpretation = a.interpretation || interpretRatio(a.name, a.value);
          const bInterpretation = b.interpretation || interpretRatio(b.name, b.value);
          const statusOrder = { good: 1, warning: 2, poor: 3 };
          aValue = statusOrder[aInterpretation.status];
          bValue = statusOrder[bInterpretation.status];
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const toggleExpanded = (metricName: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(metricName)) {
      newExpanded.delete(metricName);
    } else {
      newExpanded.add(metricName);
    }
    setExpandedRows(newExpanded);
  };

  const SortIcon: React.FC<{ field: SortField }> = ({ field }) => {
    if (sortField !== field) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }

    return sortDirection === 'asc' ? (
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  const renderMetricRow = (metric: FinancialMetric) => {
    const interpretation = metric.interpretation || interpretRatio(metric.name, metric.value);
    const isExpanded = expandedRows.has(metric.name);

    return (
      <React.Fragment key={metric.name}>
        <tr className="border-b border-gray-200 hover:bg-gray-50">
          <td className="px-6 py-4">
            <div className="flex items-center">
              <button
                onClick={() => toggleExpanded(metric.name)}
                className="mr-2 text-gray-400 hover:text-gray-600"
              >
                <svg
                  className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <span className="font-medium text-gray-900">{metric.name}</span>
            </div>
          </td>
          <td className="px-6 py-4 text-right">
            <span className="text-lg font-semibold text-gray-900">
              {metric.formatted_value}
            </span>
          </td>
          <td className="px-6 py-4">
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
          </td>
          <td className="px-6 py-4">
            <CitationList citations={metric.citations} onClick={onCitationClick} />
          </td>
        </tr>
        {isExpanded && (
          <tr className="bg-gray-50">
            <td colSpan={4} className="px-6 py-4">
              <div className="ml-6">
                <p className="text-sm text-gray-700 mb-2">
                  <span className="font-medium">Interpretation:</span> {interpretation.text}
                </p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Category:</span>
                    <span className="ml-2 text-gray-900 capitalize">{metric.category}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Raw Value:</span>
                    <span className="ml-2 text-gray-900">{metric.value.toFixed(4)}</span>
                  </div>
                </div>
              </div>
            </td>
          </tr>
        )}
      </React.Fragment>
    );
  };

  if (!metrics || metrics.length === 0) {
    return (
      <Card className={className}>
        <CardContent>
          <div className="text-center py-12 text-gray-500">
            No metrics available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Financial Metrics</CardTitle>
      </CardHeader>
      <CardContent padding="none">
        {Object.entries(groupedMetrics).map(([category, categoryMetrics]) => {
          if (categoryMetrics.length === 0) return null;

          const sortedMetrics = sortMetrics(categoryMetrics);

          return (
            <div key={category} className="mb-8 last:mb-0">
              <div className="px-6 py-3 bg-gray-100 border-b border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
                  {category} Ratios ({categoryMetrics.length})
                </h3>
              </div>

              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      onClick={() => toggleSort('name')}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    >
                      <div className="flex items-center">
                        Ratio Name
                        <SortIcon field="name" />
                      </div>
                    </th>
                    <th
                      onClick={() => toggleSort('value')}
                      className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    >
                      <div className="flex items-center justify-end">
                        Value
                        <SortIcon field="value" />
                      </div>
                    </th>
                    <th
                      onClick={() => toggleSort('status')}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    >
                      <div className="flex items-center">
                        Status
                        <SortIcon field="status" />
                      </div>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Citation
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sortedMetrics.map(renderMetricRow)}
                </tbody>
              </table>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
};
