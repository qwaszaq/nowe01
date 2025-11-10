import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { FinancialMetric } from '../../types/analysis';
import { interpretRatio } from '../../lib/metricInterpretation';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';

interface MetricsChartsProps {
  metrics: FinancialMetric[];
  className?: string;
}

type ChartType = 'bar' | 'line' | 'radar';

export const MetricsCharts: React.FC<MetricsChartsProps> = ({ metrics, className = '' }) => {
  const [chartType, setChartType] = useState<ChartType>('bar');

  // Group metrics by category
  const liquidityMetrics = metrics.filter((m) => m.category === 'liquidity');
  const profitabilityMetrics = metrics.filter((m) => m.category === 'profitability');
  const leverageMetrics = metrics.filter((m) => m.category === 'leverage');

  // Get color based on metric status
  const getColor = (metric: FinancialMetric) => {
    const interpretation = metric.interpretation || interpretRatio(metric.name, metric.value);
    switch (interpretation.status) {
      case 'good':
        return '#16a34a';
      case 'warning':
        return '#ca8a04';
      case 'poor':
        return '#dc2626';
      default:
        return '#6b7280';
    }
  };

  const renderBarChart = (data: FinancialMetric[], title: string) => {
    if (data.length === 0) return null;

    const chartData = data.map((metric) => ({
      name: metric.name.length > 20 ? metric.name.substring(0, 20) + '...' : metric.name,
      fullName: metric.name,
      value: metric.value,
      formatted: metric.formatted_value
    }));

    return (
      <div className="mb-8" key={title}>
        <h4 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
          {title}
        </h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={100}
              tick={{ fontSize: 12 }}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                      <p className="font-medium text-gray-900">{payload[0].payload.fullName}</p>
                      <p className="text-sm text-gray-600">
                        Value: <span className="font-semibold">{payload[0].payload.formatted}</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(data[index])} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const renderLineChart = (data: FinancialMetric[], title: string) => {
    if (data.length === 0) return null;

    const chartData = data.map((metric) => ({
      name: metric.name.length > 15 ? metric.name.substring(0, 15) + '...' : metric.name,
      fullName: metric.name,
      value: metric.value,
      formatted: metric.formatted_value
    }));

    return (
      <div className="mb-8" key={title}>
        <h4 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
          {title}
        </h4>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={100}
              tick={{ fontSize: 12 }}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                      <p className="font-medium text-gray-900">{payload[0].payload.fullName}</p>
                      <p className="text-sm text-gray-600">
                        Value: <span className="font-semibold">{payload[0].payload.formatted}</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#2563eb"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const renderRadarChart = () => {
    if (metrics.length === 0) return null;

    // Take up to 8 metrics for radar chart (to avoid overcrowding)
    const radarData = metrics.slice(0, 8).map((metric) => {
      // Normalize values to 0-100 scale for better visualization
      const normalizedValue = Math.min(metric.value * 10, 100);
      return {
        metric: metric.name.length > 20 ? metric.name.substring(0, 20) + '...' : metric.name,
        fullName: metric.name,
        value: normalizedValue,
        formatted: metric.formatted_value
      };
    });

    return (
      <div className="mb-8">
        <h4 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
          Overall Metrics Overview
        </h4>
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} />
            <Radar
              name="Metrics"
              dataKey="value"
              stroke="#2563eb"
              fill="#2563eb"
              fillOpacity={0.6}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                      <p className="font-medium text-gray-900">{payload[0].payload.fullName}</p>
                      <p className="text-sm text-gray-600">
                        Value: <span className="font-semibold">{payload[0].payload.formatted}</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  if (!metrics || metrics.length === 0) {
    return (
      <Card className={className}>
        <CardContent>
          <div className="text-center py-12 text-gray-500">
            No metrics available for visualization
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Metrics Visualization</CardTitle>
          <div className="flex gap-2">
            <button
              onClick={() => setChartType('bar')}
              className={`px-3 py-1 text-sm font-medium rounded ${
                chartType === 'bar'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Bar Chart
            </button>
            <button
              onClick={() => setChartType('line')}
              className={`px-3 py-1 text-sm font-medium rounded ${
                chartType === 'line'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Line Chart
            </button>
            <button
              onClick={() => setChartType('radar')}
              className={`px-3 py-1 text-sm font-medium rounded ${
                chartType === 'radar'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Radar Chart
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {chartType === 'radar' ? (
          renderRadarChart()
        ) : (
          <>
            {chartType === 'bar' && (
              <>
                {renderBarChart(liquidityMetrics, 'Liquidity Ratios')}
                {renderBarChart(profitabilityMetrics, 'Profitability Ratios')}
                {renderBarChart(leverageMetrics, 'Leverage Ratios')}
              </>
            )}
            {chartType === 'line' && (
              <>
                {renderLineChart(liquidityMetrics, 'Liquidity Ratios')}
                {renderLineChart(profitabilityMetrics, 'Profitability Ratios')}
                {renderLineChart(leverageMetrics, 'Leverage Ratios')}
              </>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};
