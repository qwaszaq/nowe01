/**
 * TypeScript types for BI Analytics API
 */

export type KPIStatus = 'excellent' | 'good' | 'warning' | 'critical' | 'unknown';
export type KPICategory = 'liquidity' | 'profitability' | 'leverage' | 'efficiency' | 'growth' | 'risk';
export type TrendDirection = 'strong_upward' | 'upward' | 'slightly_upward' | 'stable' |
  'slightly_downward' | 'downward' | 'strong_downward' | 'volatile' | 'insufficient_data';
export type AnomalyType = 'spike' | 'drop' | 'outlier' | 'pattern_break' | 'drift' |
  'volatility_shift' | 'missing_data' | 'zero_value';
export type AnomalySeverity = 'critical' | 'high' | 'medium' | 'low';
export type PerformanceRating = 'significantly_better' | 'better' | 'slightly_better' |
  'similar' | 'slightly_worse' | 'worse' | 'significantly_worse';

// ============================================================================
// KPI Types
// ============================================================================

export interface KPIDefinition {
  kpi_id: string;
  name: string;
  description: string;
  category: KPICategory;
  formula: string;
  unit: string;
  decimal_places: number;
  threshold_type: string;
  critical_threshold?: number;
  warning_threshold?: number;
  target?: number;
  upper_bound?: number;
  data_source: string;
  frequency: string;
  is_higher_better: boolean;
  icon?: string;
  color?: string;
  chart_type: string;
}

export interface KPIResult {
  kpi_id: string;
  kpi_name: string;
  category: KPICategory;
  value: number;
  formatted_value: string;
  unit: string;
  status: KPIStatus;
  status_message: string;
  target?: number;
  target_diff?: number;
  target_diff_percent?: number;
  previous_value?: number;
  change?: number;
  change_percent?: number;
  critical_threshold?: number;
  warning_threshold?: number;
  calculated_at: string;
  data_points: number;
  confidence: number;
  insights: string[];
  alerts: string[];
}

export interface KPIDashboard {
  dashboard_id: string;
  name: string;
  description: string;
  kpis: KPIResult[];
  total_kpis: number;
  excellent_count: number;
  good_count: number;
  warning_count: number;
  critical_count: number;
  critical_alerts: string[];
  warning_alerts: string[];
  case_id?: string;
  period?: string;
  updated_at: string;
}

// ============================================================================
// Trend Analysis Types
// ============================================================================

export interface DataPoint {
  timestamp: string;
  value: number;
  period_label: string;
  metadata?: Record<string, any>;
}

export interface TrendResult {
  metric_name: string;
  direction: TrendDirection;
  confidence: number;
  slope: number;
  correlation: number;
  volatility: number;
  start_value: number;
  end_value: number;
  total_change: number;
  total_change_percent: number;
  periods: number;
  period_labels: string[];
  summary: string;
  insights: string[];
  anomalous_periods: string[];
}

export interface ForecastResult {
  metric_name: string;
  forecast_periods: number;
  predictions: DataPoint[];
  confidence_intervals: [number, number][];
  method: string;
  confidence: number;
  expected_error: number;
  historical_periods: number;
  data_quality_score: number;
  summary: string;
  warnings: string[];
}

// ============================================================================
// Anomaly Detection Types
// ============================================================================

export interface Anomaly {
  anomaly_id: string;
  metric_name: string;
  anomaly_type: AnomalyType;
  severity: AnomalySeverity;
  timestamp: string;
  period_label: string;
  value: number;
  expected_value: number;
  deviation: number;
  deviation_percent: number;
  z_score: number;
  confidence: number;
  impact_description: string;
  requires_investigation: boolean;
  detection_method: string;
  detected_at: string;
  related_anomalies: string[];
}

export interface AnomalyReport {
  metric_name: string;
  analysis_period: string;
  total_periods: number;
  anomalies: Anomaly[];
  total_anomalies: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  baseline_mean: number;
  baseline_std: number;
  anomaly_rate: number;
  patterns_detected: string[];
  recommendations: string[];
  generated_at: string;
}

// ============================================================================
// Comparative Analysis Types
// ============================================================================

export interface MetricComparison {
  metric_name: string;
  metric_category: string;
  entity_a_label: string;
  entity_a_value: number;
  entity_a_formatted: string;
  entity_b_label: string;
  entity_b_value: number;
  entity_b_formatted: string;
  absolute_difference: number;
  percent_difference: number;
  rating: PerformanceRating;
  better_entity?: string;
  is_higher_better: boolean;
  interpretation: string;
}

export interface PeriodComparison {
  comparison_type: string;
  period_a: string;
  period_b: string;
  metrics: MetricComparison[];
  total_metrics: number;
  improved_metrics: number;
  declined_metrics: number;
  stable_metrics: number;
  overall_performance: PerformanceRating;
  overall_summary: string;
  key_improvements: string[];
  key_declines: string[];
  analyzed_at: string;
}

// ============================================================================
// Request Types
// ============================================================================

export interface KPICalculationRequest {
  metrics: Record<string, number>;
  previous_metrics?: Record<string, number>;
  case_id?: string;
  period?: string;
}

export interface TrendAnalysisRequest {
  metric_name: string;
  data_points: DataPoint[];
  detect_anomalies?: boolean;
}

export interface ForecastRequest {
  metric_name: string;
  data_points: DataPoint[];
  forecast_periods?: number;
  method?: 'linear' | 'moving_average' | 'exponential';
}

export interface AnomalyDetectionRequest {
  metric_name: string;
  data_points: Array<{
    timestamp: string;
    value: number;
    period_label: string;
  }>;
  analysis_period?: string;
}

export interface PeriodComparisonRequest {
  period_a_label: string;
  period_a_metrics: Record<string, number>;
  period_b_label: string;
  period_b_metrics: Record<string, number>;
  comparison_type?: string;
  metric_metadata?: Record<string, any>;
}

// ============================================================================
// Dashboard Types
// ============================================================================

export interface BIDashboardOverview {
  case_id: string;
  period: string;
  generated_at: string;
  kpis: {
    total: number;
    excellent: number;
    good: number;
    warning: number;
    critical: number;
  };
  trends: {
    total_metrics_analyzed: number;
    upward_trends: number;
    downward_trends: number;
    stable: number;
  };
  anomalies: {
    total: number;
    critical: number;
    requires_investigation: number;
  };
  insights: string[];
  alerts: string[];
  message?: string;
}

// ============================================================================
// Chart Data Types
// ============================================================================

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
  metadata?: Record<string, any>;
}

export interface TimeSeriesData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
    fill?: boolean;
  }>;
}

export interface GaugeData {
  value: number;
  min: number;
  max: number;
  thresholds: Array<{
    value: number;
    color: string;
    label: string;
  }>;
}
