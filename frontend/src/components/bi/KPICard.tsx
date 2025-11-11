/**
 * KPI Card Component
 * Displays a single KPI with gauge visualization, status, and trends
 */

import { cn } from '../../lib/utils';
import type { KPIResult } from '../../types/bi-analytics';
import { useKPIStatusColors } from '../../hooks/useBIAnalytics';

interface KPICardProps {
  kpi: KPIResult;
  className?: string;
  onClick?: () => void;
}

export function KPICard({ kpi, className, onClick }: KPICardProps) {
  const statusColors = useKPIStatusColors();
  const colors = statusColors[kpi.status];

  // Calculate gauge percentage
  const gaugePercentage = kpi.target
    ? Math.min(Math.max((kpi.value / kpi.target) * 100, 0), 150) // Cap at 150%
    : Math.min(Math.max(kpi.value, 0), 100);

  // Determine gauge color based on status
  const gaugeColor =
    kpi.status === 'excellent' ? 'stroke-green-500' :
    kpi.status === 'good' ? 'stroke-blue-500' :
    kpi.status === 'warning' ? 'stroke-yellow-500' :
    kpi.status === 'critical' ? 'stroke-red-500' :
    'stroke-gray-400';

  return (
    <div
      className={cn(
        'group relative rounded-xl border-2 p-6 shadow-lg hover:shadow-xl transition-all duration-300',
        colors.bg,
        colors.border,
        onClick && 'cursor-pointer hover:scale-105',
        className
      )}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-gray-600 tracking-wide mb-1">
            {kpi.kpi_name}
          </h3>
          <div className="flex items-baseline gap-2">
            <span className={cn('text-3xl font-mono font-bold tracking-tight', colors.text)}>
              {kpi.formatted_value}
            </span>
          </div>
        </div>

        {/* Status badge */}
        <div
          className={cn(
            'px-3 py-1 rounded-full text-xs font-semibold tracking-wide',
            colors.bg,
            colors.text
          )}
        >
          {kpi.status.toUpperCase()}
        </div>
      </div>

      {/* Gauge visualization */}
      <div className="relative w-full h-3 bg-gray-200 rounded-full overflow-hidden mb-4">
        <div
          className={cn(
            'absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out',
            kpi.status === 'excellent' ? 'bg-green-500' :
            kpi.status === 'good' ? 'bg-blue-500' :
            kpi.status === 'warning' ? 'bg-yellow-500' :
            kpi.status === 'critical' ? 'bg-red-500' :
            'bg-gray-400'
          )}
          style={{ width: `${Math.min(gaugePercentage, 100)}%` }}
        />

        {/* Target marker */}
        {kpi.target && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-gray-700"
            style={{ left: '100%' }}
          >
            <div className="absolute top-1/2 left-0 -translate-x-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-gray-700 border-2 border-white" />
          </div>
        )}
      </div>

      {/* Status message */}
      <p className="text-sm text-gray-700 mb-3">
        {kpi.status_message}
      </p>

      {/* Target info */}
      {kpi.target && (
        <div className="flex items-center justify-between text-xs text-gray-600 mb-3 pb-3 border-b border-gray-200">
          <span>Target: {kpi.target.toFixed(2)}{kpi.unit === '%' ? '%' : ''}</span>
          {kpi.target_diff_percent !== undefined && (
            <span className={cn(
              'font-semibold',
              kpi.target_diff_percent > 0 ? 'text-green-600' : 'text-red-600'
            )}>
              {kpi.target_diff_percent > 0 ? '+' : ''}{kpi.target_diff_percent.toFixed(1)}% vs target
            </span>
          )}
        </div>
      )}

      {/* Change from previous */}
      {kpi.previous_value !== undefined && kpi.change_percent !== undefined && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-gray-600">vs Previous:</span>
          <div className={cn(
            'flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold',
            kpi.change_percent > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          )}>
            {kpi.change_percent > 0 ? '↑' : '↓'}
            <span>{Math.abs(kpi.change_percent).toFixed(1)}%</span>
          </div>
        </div>
      )}

      {/* Thresholds */}
      {(kpi.critical_threshold || kpi.warning_threshold) && (
        <div className="text-xs text-gray-500 space-y-1 mb-3">
          {kpi.critical_threshold && (
            <div className="flex items-center justify-between">
              <span>Critical:</span>
              <span className="font-mono">{kpi.critical_threshold.toFixed(2)}</span>
            </div>
          )}
          {kpi.warning_threshold && (
            <div className="flex items-center justify-between">
              <span>Warning:</span>
              <span className="font-mono">{kpi.warning_threshold.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}

      {/* Insights */}
      {kpi.insights.length > 0 && (
        <div className="space-y-1">
          {kpi.insights.slice(0, 2).map((insight, idx) => (
            <div
              key={idx}
              className="text-xs text-gray-600 flex items-start gap-1"
            >
              <span className="mt-0.5">•</span>
              <span>{insight}</span>
            </div>
          ))}
        </div>
      )}

      {/* Alerts */}
      {kpi.alerts.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          {kpi.alerts.map((alert, idx) => (
            <div
              key={idx}
              className={cn(
                'text-xs px-2 py-1 rounded mb-1',
                'bg-red-50 text-red-700 border border-red-200'
              )}
            >
              {alert}
            </div>
          ))}
        </div>
      )}

      {/* Confidence indicator */}
      <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
        <span>Confidence: {(kpi.confidence * 100).toFixed(0)}%</span>
        <span>{kpi.data_points} data points</span>
      </div>
    </div>
  );
}

/**
 * KPI Grid Component
 * Display multiple KPIs in a responsive grid
 */
interface KPIGridProps {
  kpis: KPIResult[];
  onKPIClick?: (kpi: KPIResult) => void;
  className?: string;
}

export function KPIGrid({ kpis, onKPIClick, className }: KPIGridProps) {
  if (kpis.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg font-semibold mb-2">No KPIs Available</p>
        <p className="text-sm">Configure metrics to see KPI analysis</p>
      </div>
    );
  }

  return (
    <div className={cn(
      'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6',
      className
    )}>
      {kpis.map((kpi) => (
        <KPICard
          key={kpi.kpi_id}
          kpi={kpi}
          onClick={onKPIClick ? () => onKPIClick(kpi) : undefined}
        />
      ))}
    </div>
  );
}

/**
 * KPI Summary Component
 * Shows summary statistics of KPI dashboard
 */
interface KPISummaryProps {
  dashboard: {
    total_kpis: number;
    excellent_count: number;
    good_count: number;
    warning_count: number;
    critical_count: number;
  };
  className?: string;
}

export function KPISummary({ dashboard, className }: KPISummaryProps) {
  const statusCards = [
    {
      label: 'Excellent',
      count: dashboard.excellent_count,
      color: 'from-green-500 to-emerald-600',
      icon: '✓',
    },
    {
      label: 'Good',
      count: dashboard.good_count,
      color: 'from-blue-500 to-cyan-600',
      icon: '↗',
    },
    {
      label: 'Warning',
      count: dashboard.warning_count,
      color: 'from-yellow-500 to-orange-500',
      icon: '⚠',
    },
    {
      label: 'Critical',
      count: dashboard.critical_count,
      color: 'from-red-500 to-rose-600',
      icon: '!',
    },
  ];

  return (
    <div className={cn('grid grid-cols-2 lg:grid-cols-4 gap-4', className)}>
      {statusCards.map((card) => (
        <div
          key={card.label}
          className="relative overflow-hidden rounded-xl bg-white border-2 border-gray-200 p-4 shadow-md hover:shadow-lg transition-shadow"
        >
          <div className={cn(
            'absolute inset-0 opacity-5 bg-gradient-to-br',
            card.color
          )} />
          <div className="relative">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-600 tracking-wide">
                {card.label}
              </span>
              <span className="text-2xl">{card.icon}</span>
            </div>
            <div className="text-3xl font-mono font-bold text-gray-900 tracking-tight">
              {card.count}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {dashboard.total_kpis > 0
                ? `${((card.count / dashboard.total_kpis) * 100).toFixed(0)}% of total`
                : '0% of total'
              }
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
