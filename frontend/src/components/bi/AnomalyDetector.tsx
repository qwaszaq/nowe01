/**
 * Anomaly Detection Visualization Components
 */

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { cn } from '../../lib/utils';
import type { AnomalyReport, Anomaly } from '../../types/bi-analytics';
import { useAnomalySeverityColors } from '../../hooks/useBIAnalytics';

interface AnomalyReportViewProps {
  report: AnomalyReport;
  className?: string;
}

export function AnomalyReportView({ report, className }: AnomalyReportViewProps) {
  const severityColors = useAnomalySeverityColors();

  return (
    <div className={cn('bg-white rounded-xl border-2 border-gray-200 shadow-lg p-6', className)}>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900 tracking-tight">
            Anomaly Detection: {report.metric_name}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {report.analysis_period} • {report.total_periods} periods analyzed
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-600">Anomaly Rate</div>
          <div className="text-2xl font-mono font-bold text-gray-900">
            {report.anomaly_rate.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className={cn('p-4 rounded-lg border-2', severityColors.critical.border, severityColors.critical.bg)}>
          <div className={cn('text-sm font-semibold mb-1', severityColors.critical.text)}>Critical</div>
          <div className="text-2xl font-mono font-bold text-gray-900">{report.critical_count}</div>
        </div>
        <div className={cn('p-4 rounded-lg border-2', severityColors.high.border, severityColors.high.bg)}>
          <div className={cn('text-sm font-semibold mb-1', severityColors.high.text)}>High</div>
          <div className="text-2xl font-mono font-bold text-gray-900">{report.high_count}</div>
        </div>
        <div className={cn('p-4 rounded-lg border-2', severityColors.medium.border, severityColors.medium.bg)}>
          <div className={cn('text-sm font-semibold mb-1', severityColors.medium.text)}>Medium</div>
          <div className="text-2xl font-mono font-bold text-gray-900">{report.medium_count}</div>
        </div>
        <div className={cn('p-4 rounded-lg border-2', severityColors.low.border, severityColors.low.bg)}>
          <div className={cn('text-sm font-semibold mb-1', severityColors.low.text)}>Low</div>
          <div className="text-2xl font-mono font-bold text-gray-900">{report.low_count}</div>
        </div>
      </div>

      {/* Anomalies List */}
      {report.anomalies.length > 0 && (
        <div className="space-y-3 mb-6">
          <h4 className="font-semibold text-gray-900">Detected Anomalies</h4>
          {report.anomalies.slice(0, 5).map((anomaly) => (
            <AnomalyCard key={anomaly.anomaly_id} anomaly={anomaly} />
          ))}
          {report.anomalies.length > 5 && (
            <div className="text-sm text-gray-600 text-center py-2">
              +{report.anomalies.length - 5} more anomalies
            </div>
          )}
        </div>
      )}

      {/* Patterns */}
      {report.patterns_detected.length > 0 && (
        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 mb-2">Patterns Detected</h4>
          <div className="space-y-2">
            {report.patterns_detected.map((pattern, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="mt-0.5">•</span>
                <span>{pattern}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {report.recommendations.length > 0 && (
        <div className="p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
          <h4 className="font-semibold text-blue-900 mb-2">Recommendations</h4>
          <div className="space-y-2">
            {report.recommendations.map((rec, idx) => (
              <div key={idx} className="text-sm text-blue-800">
                {rec}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface AnomalyCardProps {
  anomaly: Anomaly;
  className?: string;
}

export function AnomalyCard({ anomaly, className }: AnomalyCardProps) {
  const severityColors = useAnomalySeverityColors();
  const colors = severityColors[anomaly.severity];

  return (
    <div className={cn(
      'p-4 rounded-lg border-2',
      colors.border,
      colors.bg,
      className
    )}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn(
              'px-2 py-0.5 rounded text-xs font-bold uppercase',
              colors.badge,
              'text-white'
            )}>
              {anomaly.severity}
            </span>
            <span className="text-xs font-semibold text-gray-600">
              {anomaly.anomaly_type.replace(/_/g, ' ')}
            </span>
          </div>
          <div className="text-sm font-semibold text-gray-900">
            {anomaly.period_label}
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-mono font-bold text-gray-900">
            {anomaly.value.toFixed(2)}
          </div>
          <div className="text-xs text-gray-600">
            Expected: {anomaly.expected_value.toFixed(2)}
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-700 mb-2">
        {anomaly.impact_description}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>Deviation: {anomaly.deviation_percent.toFixed(1)}%</span>
        <span>Z-score: {anomaly.z_score.toFixed(2)}</span>
        <span>Confidence: {(anomaly.confidence * 100).toFixed(0)}%</span>
      </div>

      {anomaly.requires_investigation && (
        <div className="mt-2 pt-2 border-t border-gray-300">
          <div className="text-xs font-semibold text-red-700">
            ⚠️ Requires Investigation
          </div>
        </div>
      )}
    </div>
  );
}
