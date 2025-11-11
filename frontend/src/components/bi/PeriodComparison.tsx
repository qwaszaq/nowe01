/**
 * Period Comparison Components
 */

import { cn } from '../../lib/utils';
import type { PeriodComparison as PeriodComparisonType, MetricComparison } from '../../types/bi-analytics';

interface PeriodComparisonViewProps {
  comparison: PeriodComparisonType;
  className?: string;
}

export function PeriodComparisonView({ comparison, className }: PeriodComparisonViewProps) {
  const getPerformanceColor = (rating: string) => {
    if (rating.includes('better')) return 'text-green-600';
    if (rating.includes('worse')) return 'text-red-600';
    return 'text-gray-600';
  };

  const getPerformanceBg = (rating: string) => {
    if (rating.includes('significantly_better')) return 'bg-green-100 border-green-300';
    if (rating.includes('better')) return 'bg-green-50 border-green-200';
    if (rating.includes('significantly_worse')) return 'bg-red-100 border-red-300';
    if (rating.includes('worse')) return 'bg-red-50 border-red-200';
    return 'bg-gray-50 border-gray-200';
  };

  return (
    <div className={cn('bg-white rounded-xl border-2 border-gray-200 shadow-lg p-6', className)}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold text-gray-900 tracking-tight">
              Period Comparison
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {comparison.period_a} vs {comparison.period_b}
            </p>
          </div>
          <div className={cn(
            'px-4 py-2 rounded-lg font-semibold',
            getPerformanceBg(comparison.overall_performance)
          )}>
            <span className={getPerformanceColor(comparison.overall_performance)}>
              {comparison.overall_performance.replace(/_/g, ' ').toUpperCase()}
            </span>
          </div>
        </div>

        <p className="text-sm text-gray-700">
          {comparison.overall_summary}
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-green-50 border-2 border-green-200 rounded-lg">
          <div className="text-sm text-green-700 font-semibold mb-1">Improved</div>
          <div className="text-2xl font-mono font-bold text-gray-900">{comparison.improved_metrics}</div>
          <div className="text-xs text-green-600 mt-1">
            {((comparison.improved_metrics / comparison.total_metrics) * 100).toFixed(0)}% of total
          </div>
        </div>
        <div className="p-4 bg-gray-50 border-2 border-gray-200 rounded-lg">
          <div className="text-sm text-gray-700 font-semibold mb-1">Stable</div>
          <div className="text-2xl font-mono font-bold text-gray-900">{comparison.stable_metrics}</div>
          <div className="text-xs text-gray-600 mt-1">
            {((comparison.stable_metrics / comparison.total_metrics) * 100).toFixed(0)}% of total
          </div>
        </div>
        <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
          <div className="text-sm text-red-700 font-semibold mb-1">Declined</div>
          <div className="text-2xl font-mono font-bold text-gray-900">{comparison.declined_metrics}</div>
          <div className="text-xs text-red-600 mt-1">
            {((comparison.declined_metrics / comparison.total_metrics) * 100).toFixed(0)}% of total
          </div>
        </div>
      </div>

      {/* Key Changes */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {comparison.key_improvements.length > 0 && (
          <div>
            <h4 className="font-semibold text-green-800 mb-2">📈 Key Improvements</h4>
            <div className="space-y-1">
              {comparison.key_improvements.map((imp, idx) => (
                <div key={idx} className="text-sm text-green-700 bg-green-50 p-2 rounded">
                  {imp}
                </div>
              ))}
            </div>
          </div>
        )}
        {comparison.key_declines.length > 0 && (
          <div>
            <h4 className="font-semibold text-red-800 mb-2">📉 Key Declines</h4>
            <div className="space-y-1">
              {comparison.key_declines.map((dec, idx) => (
                <div key={idx} className="text-sm text-red-700 bg-red-50 p-2 rounded">
                  {dec}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Detailed Metrics Table */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-3">Detailed Metric Comparison</h4>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-300">
                <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">Metric</th>
                <th className="text-right py-2 px-3 text-sm font-semibold text-gray-700">
                  {comparison.period_a}
                </th>
                <th className="text-right py-2 px-3 text-sm font-semibold text-gray-700">
                  {comparison.period_b}
                </th>
                <th className="text-right py-2 px-3 text-sm font-semibold text-gray-700">Change</th>
                <th className="text-center py-2 px-3 text-sm font-semibold text-gray-700">Rating</th>
              </tr>
            </thead>
            <tbody>
              {comparison.metrics.map((metric, idx) => (
                <MetricComparisonRow key={idx} metric={metric} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

interface MetricComparisonRowProps {
  metric: MetricComparison;
}

function MetricComparisonRow({ metric }: MetricComparisonRowProps) {
  const getChangeColor = (percent: number) => {
    if (Math.abs(percent) < 1) return 'text-gray-600';
    return percent > 0 ? 'text-green-600' : 'text-red-600';
  };

  const getRatingBadge = (rating: string) => {
    if (rating.includes('better')) {
      return 'bg-green-100 text-green-700 border-green-300';
    }
    if (rating.includes('worse')) {
      return 'bg-red-100 text-red-700 border-red-300';
    }
    return 'bg-gray-100 text-gray-700 border-gray-300';
  };

  return (
    <tr className="border-b border-gray-200 hover:bg-gray-50">
      <td className="py-3 px-3">
        <div className="font-semibold text-sm text-gray-900">{metric.metric_name}</div>
        <div className="text-xs text-gray-600">{metric.metric_category}</div>
      </td>
      <td className="py-3 px-3 text-right">
        <span className="font-mono text-sm text-gray-900">{metric.entity_a_formatted}</span>
      </td>
      <td className="py-3 px-3 text-right">
        <span className="font-mono text-sm text-gray-900">{metric.entity_b_formatted}</span>
      </td>
      <td className="py-3 px-3 text-right">
        <div className={cn('font-mono text-sm font-semibold', getChangeColor(metric.percent_difference))}>
          {metric.percent_difference > 0 ? '+' : ''}{metric.percent_difference.toFixed(1)}%
        </div>
      </td>
      <td className="py-3 px-3 text-center">
        <span className={cn(
          'inline-block px-2 py-1 rounded text-xs font-semibold border',
          getRatingBadge(metric.rating)
        )}>
          {metric.rating.replace(/_/g, ' ')}
        </span>
      </td>
    </tr>
  );
}

/**
 * Compact Period Comparison Card
 */
interface PeriodComparisonCardProps {
  comparison: PeriodComparisonType;
  onClick?: () => void;
  className?: string;
}

export function PeriodComparisonCard({ comparison, onClick, className }: PeriodComparisonCardProps) {
  const getPerformanceColor = (rating: string) => {
    if (rating.includes('better')) return 'text-green-600';
    if (rating.includes('worse')) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div
      className={cn(
        'bg-white rounded-xl border-2 border-gray-200 p-4 shadow-md hover:shadow-lg transition-shadow',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-900">
          {comparison.period_a} vs {comparison.period_b}
        </div>
        <div className={cn('text-xs font-bold', getPerformanceColor(comparison.overall_performance))}>
          {comparison.overall_performance.replace(/_/g, ' ').toUpperCase()}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center mb-3">
        <div>
          <div className="text-xs text-gray-600">Improved</div>
          <div className="text-lg font-mono font-bold text-green-600">{comparison.improved_metrics}</div>
        </div>
        <div>
          <div className="text-xs text-gray-600">Stable</div>
          <div className="text-lg font-mono font-bold text-gray-600">{comparison.stable_metrics}</div>
        </div>
        <div>
          <div className="text-xs text-gray-600">Declined</div>
          <div className="text-lg font-mono font-bold text-red-600">{comparison.declined_metrics}</div>
        </div>
      </div>

      <p className="text-xs text-gray-700 line-clamp-2">
        {comparison.overall_summary}
      </p>
    </div>
  );
}
