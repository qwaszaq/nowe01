/**
 * Trend Chart Component
 * Visualizes time-series data with trend lines and forecast overlays
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
  ReferenceLine,
} from 'recharts';
import { cn } from '../../lib/utils';
import type { TrendResult, ForecastResult, DataPoint } from '../../types/bi-analytics';
import { useTrendDirectionStyles } from '../../hooks/useBIAnalytics';

interface TrendChartProps {
  metricName: string;
  data: DataPoint[];
  trendResult?: TrendResult;
  forecastResult?: ForecastResult;
  showForecast?: boolean;
  className?: string;
}

export function TrendChart({
  metricName,
  data,
  trendResult,
  forecastResult,
  showForecast = false,
  className,
}: TrendChartProps) {
  const trendStyles = useTrendDirectionStyles();

  // Combine historical and forecast data
  const chartData = [...data.map(d => ({
    period: d.period_label,
    value: d.value,
    forecast: null as number | null,
    lowerBound: null as number | null,
    upperBound: null as number | null,
  }))];

  if (showForecast && forecastResult) {
    forecastResult.predictions.forEach((pred, idx) => {
      const [lower, upper] = forecastResult.confidence_intervals[idx] || [0, 0];
      chartData.push({
        period: pred.period_label,
        value: null as number | null,
        forecast: pred.value,
        lowerBound: lower,
        upperBound: upper,
      });
    });
  }

  const trendColor = trendResult
    ? trendStyles[trendResult.direction]?.color?.replace('text-', '') || 'blue-500'
    : 'blue-500';

  return (
    <div className={cn('bg-white rounded-xl border-2 border-gray-200 shadow-lg p-6', className)}>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900 tracking-tight">
            {metricName} Trend Analysis
          </h3>
          {trendResult && (
            <div className="flex items-center gap-3 mt-2">
              <div className={cn(
                'flex items-center gap-2 px-3 py-1 rounded-full text-sm font-semibold',
                trendStyles[trendResult.direction]?.bg
              )}>
                <span>{trendStyles[trendResult.direction]?.icon}</span>
                <span className={trendStyles[trendResult.direction]?.color}>
                  {trendStyles[trendResult.direction]?.label}
                </span>
              </div>
              <span className="text-sm text-gray-600">
                {trendResult.total_change > 0 ? '+' : ''}{trendResult.total_change_percent.toFixed(1)}%
              </span>
            </div>
          )}
        </div>

        {forecastResult && (
          <div className="text-right">
            <div className="text-sm text-gray-600">Forecast Confidence</div>
            <div className="text-2xl font-mono font-bold text-gray-900">
              {(forecastResult.confidence * 100).toFixed(0)}%
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="period"
              stroke="#6b7280"
              style={{ fontSize: '12px', fontWeight: 600 }}
            />
            <YAxis
              stroke="#6b7280"
              style={{ fontSize: '12px', fontWeight: 600 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 600,
              }}
              formatter={(value: any) => [value?.toFixed(2) || 'N/A', '']}
            />
            <Legend wrapperStyle={{ fontSize: '12px', fontWeight: 600 }} />

            {/* Confidence interval area */}
            {showForecast && forecastResult && (
              <Area
                type="monotone"
                dataKey="upperBound"
                stroke="none"
                fill="#93c5fd"
                fillOpacity={0.2}
                name="Confidence Range"
              />
            )}

            {/* Historical data line */}
            <Line
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', r: 4 }}
              name="Actual"
              connectNulls={false}
            />

            {/* Forecast line */}
            {showForecast && forecastResult && (
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="#f59e0b"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#f59e0b', r: 3 }}
                name="Forecast"
                connectNulls={false}
              />
            )}

            {/* Target line */}
            {trendResult && trendResult.start_value && (
              <ReferenceLine
                y={trendResult.start_value}
                stroke="#9ca3af"
                strokeDasharray="3 3"
                label={{ value: 'Baseline', position: 'right', style: { fontSize: 11 } }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Statistics */}
      {trendResult && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200">
          <div>
            <div className="text-xs text-gray-600 mb-1">Correlation</div>
            <div className="text-lg font-mono font-bold text-gray-900">
              {trendResult.correlation.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">Volatility</div>
            <div className="text-lg font-mono font-bold text-gray-900">
              {(trendResult.volatility * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">Periods</div>
            <div className="text-lg font-mono font-bold text-gray-900">
              {trendResult.periods}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">Confidence</div>
            <div className="text-lg font-mono font-bold text-gray-900">
              {(trendResult.confidence * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      )}

      {/* Insights */}
      {trendResult && trendResult.insights.length > 0 && (
        <div className="mt-4 space-y-2">
          {trendResult.insights.map((insight, idx) => (
            <div key={idx} className="flex items-start gap-2 text-sm text-gray-700">
              <span className="mt-0.5">•</span>
              <span>{insight}</span>
            </div>
          ))}
        </div>
      )}

      {/* Forecast warnings */}
      {showForecast && forecastResult && forecastResult.warnings.length > 0 && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="text-sm font-semibold text-yellow-800 mb-1">Forecast Warnings:</div>
          {forecastResult.warnings.map((warning, idx) => (
            <div key={idx} className="text-sm text-yellow-700">
              {warning}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Mini Trend Sparkline
 * Compact trend visualization for cards
 */
interface TrendSparklineProps {
  data: DataPoint[];
  trendDirection?: string;
  className?: string;
}

export function TrendSparkline({ data, trendDirection, className }: TrendSparklineProps) {
  const values = data.map(d => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;

  const points = data.map((d, idx) => {
    const x = (idx / (data.length - 1)) * 100;
    const y = 100 - ((d.value - min) / (range || 1)) * 100;
    return `${x},${y}`;
  }).join(' ');

  const trendStyles = useTrendDirectionStyles();
  const color = trendDirection
    ? trendStyles[trendDirection as keyof typeof trendStyles]?.color?.replace('text-', '') || 'blue-500'
    : 'blue-500';

  return (
    <div className={cn('relative w-full h-12', className)}>
      <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        {/* Area fill */}
        <polygon
          points={`0,100 ${points} 100,100`}
          fill={`url(#gradient-${trendDirection})`}
          opacity="0.2"
        />

        {/* Line */}
        <polyline
          points={points}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={color}
        />

        {/* Gradient definition */}
        <defs>
          <linearGradient id={`gradient-${trendDirection}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.5" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
}
