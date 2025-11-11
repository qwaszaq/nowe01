/**
 * BI Dashboard Page
 * Comprehensive Business Intelligence dashboard with KPIs, trends, and analytics
 */

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Tab } from '@headlessui/react';
import { cn } from '../lib/utils';
import { KPIGrid, KPISummary } from '../components/bi/KPICard';
import { TrendChart } from '../components/bi/TrendChart';
import { AnomalyReportView } from '../components/bi/AnomalyDetector';
import { PeriodComparisonView } from '../components/bi/PeriodComparison';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import {
  useKPIDefinitions,
  useCalculateKPIDashboard,
  useAnalyzeTrend,
  useGenerateForecast,
  useDetectAnomalies,
  useComparePeriods,
  useBIDashboardOverview,
} from '../hooks/useBIAnalytics';
import type { KPIDashboard as KPIDashboardType, DataPoint } from '../types/bi-analytics';

export default function BIDashboard() {
  const { caseId } = useParams<{ caseId: string }>();
  const [activeTab, setActiveTab] = useState(0);
  const [selectedPeriod, setSelectedPeriod] = useState('current');

  // For demo purposes - would integrate with actual case data
  const mockMetrics = {
    current_ratio: 2.5,
    quick_ratio: 1.8,
    cash_ratio: 0.6,
    net_profit_margin: 12.5,
    roa: 8.3,
    roe: 15.2,
    gross_profit_margin: 35.8,
    debt_to_equity: 0.8,
    debt_ratio: 42.0,
    interest_coverage: 4.5,
  };

  const previousMetrics = {
    current_ratio: 2.2,
    quick_ratio: 1.5,
    cash_ratio: 0.5,
    net_profit_margin: 11.0,
    roa: 7.5,
    roe: 14.0,
    gross_profit_margin: 34.0,
    debt_to_equity: 0.9,
    debt_ratio: 45.0,
    interest_coverage: 4.0,
  };

  // Mock time-series data for trends
  const mockTrendData: DataPoint[] = [
    { timestamp: '2024-01-01T00:00:00Z', value: 2.2, period_label: 'Q1 2024' },
    { timestamp: '2024-04-01T00:00:00Z', value: 2.3, period_label: 'Q2 2024' },
    { timestamp: '2024-07-01T00:00:00Z', value: 2.4, period_label: 'Q3 2024' },
    { timestamp: '2024-10-01T00:00:00Z', value: 2.5, period_label: 'Q4 2024' },
  ];

  // Fetch KPI definitions
  const { data: kpiDefinitions, isLoading: defsLoading } = useKPIDefinitions();

  // Calculate KPI dashboard
  const calculateKPIs = useCalculateKPIDashboard();
  const [kpiDashboard, setKPIDashboard] = useState<KPIDashboardType | null>(null);

  // Analyze trends
  const analyzeTrend = useAnalyzeTrend();
  const generateForecast = useGenerateForecast();

  // Detect anomalies
  const detectAnomalies = useDetectAnomalies();

  // Compare periods
  const comparePeriods = useComparePeriods();

  // Calculate KPIs on load
  useState(() => {
    if (!kpiDashboard) {
      calculateKPIs.mutate({
        metrics: mockMetrics,
        previous_metrics: previousMetrics,
        case_id: caseId,
        period: selectedPeriod,
      }, {
        onSuccess: (data) => setKPIDashboard(data),
      });
    }
  });

  const tabs = ['Overview', 'KPIs', 'Trends & Forecasts', 'Anomalies', 'Comparisons'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-900 text-white shadow-xl">
        <div className="px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold tracking-tight">
                BI Analytics Dashboard
              </h1>
              <p className="mt-2 text-slate-200">
                Business Intelligence • KPIs • Trends • Anomalies • Comparisons
              </p>
            </div>

            {/* Period selector */}
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-white/50"
            >
              <option value="current">Current Period</option>
              <option value="ytd">Year to Date</option>
              <option value="q1">Q1 2024</option>
              <option value="q2">Q2 2024</option>
              <option value="q3">Q3 2024</option>
              <option value="q4">Q4 2024</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="px-4 sm:px-6 lg:px-8">
          <Tab.Group selectedIndex={activeTab} onChange={setActiveTab}>
            <Tab.List className="flex gap-4">
              {tabs.map((tab) => (
                <Tab
                  key={tab}
                  className={({ selected }) =>
                    cn(
                      'py-4 px-6 text-sm font-semibold border-b-2 transition-colors focus:outline-none',
                      selected
                        ? 'border-slate-700 text-slate-900'
                        : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                    )
                  }
                >
                  {tab}
                </Tab>
              ))}
            </Tab.List>
          </Tab.Group>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        <Tab.Group selectedIndex={activeTab} onChange={setActiveTab}>
          <Tab.Panels>
            {/* Overview Tab */}
            <Tab.Panel>
              <div className="space-y-8">
                {/* KPI Summary */}
                {kpiDashboard && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">KPI Summary</h2>
                    <KPISummary dashboard={kpiDashboard} />
                  </div>
                )}

                {/* Quick Stats */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white rounded-xl border-2 border-gray-200 shadow-lg p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">🎯 Performance Highlights</h3>
                    {kpiDashboard && kpiDashboard.kpis.length > 0 ? (
                      <div className="space-y-3">
                        {kpiDashboard.kpis
                          .filter(kpi => kpi.status === 'excellent')
                          .slice(0, 3)
                          .map(kpi => (
                            <div key={kpi.kpi_id} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                              <span className="text-sm font-semibold text-gray-900">{kpi.kpi_name}</span>
                              <span className="text-lg font-mono font-bold text-green-600">{kpi.formatted_value}</span>
                            </div>
                          ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600">No excellent KPIs to display</p>
                    )}
                  </div>

                  <div className="bg-white rounded-xl border-2 border-gray-200 shadow-lg p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">⚠️ Areas of Concern</h3>
                    {kpiDashboard && kpiDashboard.critical_alerts.length > 0 ? (
                      <div className="space-y-2">
                        {kpiDashboard.critical_alerts.slice(0, 3).map((alert, idx) => (
                          <div key={idx} className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                            {alert}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600">No critical alerts</p>
                    )}
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border-2 border-blue-200 p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Quick Actions</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <button
                      onClick={() => setActiveTab(1)}
                      className="p-4 bg-white rounded-lg border-2 border-blue-200 hover:border-blue-400 hover:shadow-lg transition-all text-center"
                    >
                      <div className="text-2xl mb-2">📈</div>
                      <div className="text-sm font-semibold text-gray-900">View KPIs</div>
                    </button>
                    <button
                      onClick={() => setActiveTab(2)}
                      className="p-4 bg-white rounded-lg border-2 border-blue-200 hover:border-blue-400 hover:shadow-lg transition-all text-center"
                    >
                      <div className="text-2xl mb-2">📉</div>
                      <div className="text-sm font-semibold text-gray-900">Analyze Trends</div>
                    </button>
                    <button
                      onClick={() => setActiveTab(3)}
                      className="p-4 bg-white rounded-lg border-2 border-blue-200 hover:border-blue-400 hover:shadow-lg transition-all text-center"
                    >
                      <div className="text-2xl mb-2">🔍</div>
                      <div className="text-sm font-semibold text-gray-900">Find Anomalies</div>
                    </button>
                    <button
                      onClick={() => setActiveTab(4)}
                      className="p-4 bg-white rounded-lg border-2 border-blue-200 hover:border-blue-400 hover:shadow-lg transition-all text-center"
                    >
                      <div className="text-2xl mb-2">⚖️</div>
                      <div className="text-sm font-semibold text-gray-900">Compare Periods</div>
                    </button>
                  </div>
                </div>
              </div>
            </Tab.Panel>

            {/* KPIs Tab */}
            <Tab.Panel>
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Key Performance Indicators</h2>
                  <p className="text-sm text-gray-600">
                    Real-time KPI monitoring with threshold-based alerts and status evaluation
                  </p>
                </div>

                {calculateKPIs.isLoading && <LoadingSkeleton variant="card" count={8} />}
                {calculateKPIs.error && <ErrorMessage error={calculateKPIs.error} />}
                {kpiDashboard && <KPIGrid kpis={kpiDashboard.kpis} />}
              </div>
            </Tab.Panel>

            {/* Trends & Forecasts Tab */}
            <Tab.Panel>
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Trend Analysis & Forecasting</h2>
                  <p className="text-sm text-gray-600">
                    Time-series analysis with predictive forecasting and pattern detection
                  </p>
                </div>

                <div className="bg-white rounded-xl border-2 border-gray-200 shadow-lg p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">Select Metric for Analysis</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {['Current Ratio', 'Net Profit Margin', 'ROE', 'Debt-to-Equity'].map((metric) => (
                      <button
                        key={metric}
                        onClick={() => {
                          analyzeTrend.mutate({
                            metric_name: metric,
                            data_points: mockTrendData,
                            detect_anomalies: true,
                          });
                        }}
                        className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-400 hover:shadow-lg transition-all text-center"
                      >
                        <div className="text-sm font-semibold text-gray-900">{metric}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {analyzeTrend.data && (
                  <TrendChart
                    metricName={analyzeTrend.data.metric_name}
                    data={mockTrendData}
                    trendResult={analyzeTrend.data}
                  />
                )}

                <div className="text-center text-sm text-gray-600">
                  💡 Tip: Select a metric above to view its trend analysis and forecast
                </div>
              </div>
            </Tab.Panel>

            {/* Anomalies Tab */}
            <Tab.Panel>
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Anomaly Detection</h2>
                  <p className="text-sm text-gray-600">
                    Multi-method anomaly detection with severity classification and recommendations
                  </p>
                </div>

                <div className="bg-white rounded-xl border-2 border-gray-200 shadow-lg p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">Detect Anomalies</h3>
                  <button
                    onClick={() => {
                      detectAnomalies.mutate({
                        metric_name: 'Current Ratio',
                        data_points: mockTrendData.map(d => ({
                          timestamp: d.timestamp,
                          value: d.value,
                          period_label: d.period_label,
                        })),
                        analysis_period: 'Last 12 Months',
                      });
                    }}
                    className="px-6 py-3 bg-gradient-to-r from-slate-700 to-slate-900 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                  >
                    🔍 Run Anomaly Detection
                  </button>
                </div>

                {detectAnomalies.isLoading && <LoadingSkeleton variant="card" count={1} />}
                {detectAnomalies.data && <AnomalyReportView report={detectAnomalies.data} />}

                {!detectAnomalies.data && !detectAnomalies.isLoading && (
                  <div className="text-center py-12 text-gray-500">
                    <p className="text-lg font-semibold mb-2">No Anomaly Report Yet</p>
                    <p className="text-sm">Click the button above to run anomaly detection</p>
                  </div>
                )}
              </div>
            </Tab.Panel>

            {/* Comparisons Tab */}
            <Tab.Panel>
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Period Comparisons</h2>
                  <p className="text-sm text-gray-600">
                    Period-over-period analysis with performance ratings and insights
                  </p>
                </div>

                <div className="bg-white rounded-xl border-2 border-gray-200 shadow-lg p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">Compare Periods</h3>
                  <button
                    onClick={() => {
                      comparePeriods.mutate({
                        period_a_label: 'Q3 2024',
                        period_a_metrics: previousMetrics,
                        period_b_label: 'Q4 2024',
                        period_b_metrics: mockMetrics,
                        comparison_type: 'sequential_period',
                      });
                    }}
                    className="px-6 py-3 bg-gradient-to-r from-slate-700 to-slate-900 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                  >
                    ⚖️ Compare Q3 vs Q4 2024
                  </button>
                </div>

                {comparePeriods.isLoading && <LoadingSkeleton variant="card" count={1} />}
                {comparePeriods.data && <PeriodComparisonView comparison={comparePeriods.data} />}

                {!comparePeriods.data && !comparePeriods.isLoading && (
                  <div className="text-center py-12 text-gray-500">
                    <p className="text-lg font-semibold mb-2">No Comparison Report Yet</p>
                    <p className="text-sm">Click the button above to compare periods</p>
                  </div>
                )}
              </div>
            </Tab.Panel>
          </Tab.Panels>
        </Tab.Group>
      </div>
    </div>
  );
}
