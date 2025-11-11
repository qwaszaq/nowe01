/**
 * React hooks for BI Analytics API
 */

import { useQuery, useMutation, UseQueryOptions } from '@tanstack/react-query';
import { api } from '../lib/api';
import type {
  KPIDashboard,
  KPICalculationRequest,
  KPIDefinition,
  TrendResult,
  TrendAnalysisRequest,
  ForecastResult,
  ForecastRequest,
  AnomalyReport,
  AnomalyDetectionRequest,
  PeriodComparison,
  PeriodComparisonRequest,
  BIDashboardOverview,
} from '../types/bi-analytics';

// ============================================================================
// KPI Hooks
// ============================================================================

/**
 * Get all KPI definitions
 */
export function useKPIDefinitions(category?: string) {
  return useQuery<KPIDefinition[]>({
    queryKey: ['kpi-definitions', category],
    queryFn: async () => {
      const params = category ? `?category=${category}` : '';
      const response = await api.get(`/analytics/kpis/definitions${params}`);
      return response.data;
    },
  });
}

/**
 * Get specific KPI definition
 */
export function useKPIDefinition(kpiId: string) {
  return useQuery<KPIDefinition>({
    queryKey: ['kpi-definition', kpiId],
    queryFn: async () => {
      const response = await api.get(`/analytics/kpis/${kpiId}/definition`);
      return response.data;
    },
    enabled: !!kpiId,
  });
}

/**
 * Calculate KPI dashboard
 */
export function useCalculateKPIDashboard() {
  return useMutation<KPIDashboard, Error, KPICalculationRequest>({
    mutationFn: async (request) => {
      const response = await api.post('/analytics/kpis/calculate', request);
      return response.data;
    },
  });
}

/**
 * Get pre-calculated KPI dashboard for a case
 */
export function useKPIDashboard(
  caseId?: string,
  period?: string,
  options?: UseQueryOptions<KPIDashboard>
) {
  return useQuery<KPIDashboard>({
    queryKey: ['kpi-dashboard', caseId, period],
    queryFn: async () => {
      // This would call a GET endpoint if we had one
      // For now, we'll need to calculate it via POST with stored data
      // Placeholder - would integrate with actual data retrieval
      throw new Error('KPI dashboard retrieval not implemented - use useCalculateKPIDashboard');
    },
    enabled: !!caseId && (options?.enabled ?? true),
    ...options,
  });
}

// ============================================================================
// Trend Analysis Hooks
// ============================================================================

/**
 * Analyze trend for a metric
 */
export function useAnalyzeTrend() {
  return useMutation<TrendResult, Error, TrendAnalysisRequest>({
    mutationFn: async (request) => {
      const response = await api.post('/analytics/trends/analyze', request);
      return response.data;
    },
  });
}

/**
 * Generate forecast for a metric
 */
export function useGenerateForecast() {
  return useMutation<ForecastResult, Error, ForecastRequest>({
    mutationFn: async (request) => {
      const response = await api.post('/analytics/trends/forecast', request);
      return response.data;
    },
  });
}

// ============================================================================
// Anomaly Detection Hooks
// ============================================================================

/**
 * Detect anomalies in metric data
 */
export function useDetectAnomalies() {
  return useMutation<AnomalyReport, Error, AnomalyDetectionRequest>({
    mutationFn: async (request) => {
      const response = await api.post('/analytics/anomalies/detect', request);
      return response.data;
    },
  });
}

/**
 * Get anomaly summary for a case
 */
export function useAnomalySummary(caseId?: string, period?: string) {
  return useQuery({
    queryKey: ['anomaly-summary', caseId, period],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (caseId) params.append('case_id', caseId);
      if (period) params.append('period', period);

      const response = await api.get(`/analytics/anomalies/summary?${params}`);
      return response.data;
    },
    enabled: !!caseId,
  });
}

// ============================================================================
// Comparative Analysis Hooks
// ============================================================================

/**
 * Compare two periods
 */
export function useComparePeriods() {
  return useMutation<PeriodComparison, Error, PeriodComparisonRequest>({
    mutationFn: async (request) => {
      const response = await api.post('/analytics/compare/periods', request);
      return response.data;
    },
  });
}

/**
 * Benchmark comparison
 */
export function useBenchmarkComparison(
  caseId?: string,
  industry?: string,
  period?: string
) {
  return useQuery({
    queryKey: ['benchmark-comparison', caseId, industry, period],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (caseId) params.append('case_id', caseId);
      if (industry) params.append('industry', industry);
      if (period) params.append('period', period);

      const response = await api.get(`/analytics/compare/benchmark?${params}`);
      return response.data;
    },
    enabled: !!caseId,
  });
}

// ============================================================================
// Drill-Down Hooks
// ============================================================================

/**
 * Get available drill-down hierarchies
 */
export function useDrillDownHierarchies() {
  return useQuery<Record<string, string[]>>({
    queryKey: ['drill-down-hierarchies'],
    queryFn: async () => {
      const response = await api.get('/analytics/drilldown/hierarchy');
      return response.data;
    },
  });
}

/**
 * Aggregate metrics at specific level
 */
export function useAggregateMetrics() {
  return useMutation({
    mutationFn: async (params: {
      metric_name: string;
      level: string;
      aggregation_type?: string;
      group_by?: string;
    }) => {
      const queryParams = new URLSearchParams({
        metric_name: params.metric_name,
        level: params.level,
      });
      if (params.aggregation_type) {
        queryParams.append('aggregation_type', params.aggregation_type);
      }
      if (params.group_by) {
        queryParams.append('group_by', params.group_by);
      }

      const response = await api.post(`/analytics/drilldown/aggregate?${queryParams}`);
      return response.data;
    },
  });
}

// ============================================================================
// Integrated Dashboard Hooks
// ============================================================================

/**
 * Get complete BI dashboard overview
 */
export function useBIDashboardOverview(caseId?: string, period?: string) {
  return useQuery<BIDashboardOverview>({
    queryKey: ['bi-dashboard-overview', caseId, period],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (caseId) params.append('case_id', caseId);
      if (period) params.append('period', period);

      const response = await api.get(`/analytics/dashboard/overview?${params}`);
      return response.data;
    },
    enabled: !!caseId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

/**
 * Check analytics engine health
 */
export function useAnalyticsHealth() {
  return useQuery({
    queryKey: ['analytics-health'],
    queryFn: async () => {
      const response = await api.get('/analytics/health');
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
}

// ============================================================================
// Helper Hooks
// ============================================================================

/**
 * Get KPI status color classes
 */
export function useKPIStatusColors() {
  return {
    excellent: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-700',
      icon: 'text-green-600',
    },
    good: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-700',
      icon: 'text-blue-600',
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-700',
      icon: 'text-yellow-600',
    },
    critical: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-700',
      icon: 'text-red-600',
    },
    unknown: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      text: 'text-gray-700',
      icon: 'text-gray-600',
    },
  };
}

/**
 * Get trend direction icon and color
 */
export function useTrendDirectionStyles() {
  return {
    strong_upward: {
      icon: '📈',
      color: 'text-green-600',
      bg: 'bg-green-50',
      label: 'Strong Upward'
    },
    upward: {
      icon: '↗️',
      color: 'text-green-500',
      bg: 'bg-green-50',
      label: 'Upward'
    },
    slightly_upward: {
      icon: '→',
      color: 'text-blue-500',
      bg: 'bg-blue-50',
      label: 'Slightly Up'
    },
    stable: {
      icon: '→',
      color: 'text-gray-500',
      bg: 'bg-gray-50',
      label: 'Stable'
    },
    slightly_downward: {
      icon: '→',
      color: 'text-orange-500',
      bg: 'bg-orange-50',
      label: 'Slightly Down'
    },
    downward: {
      icon: '↘️',
      color: 'text-red-500',
      bg: 'bg-red-50',
      label: 'Downward'
    },
    strong_downward: {
      icon: '📉',
      color: 'text-red-600',
      bg: 'bg-red-50',
      label: 'Strong Downward'
    },
    volatile: {
      icon: '📊',
      color: 'text-purple-500',
      bg: 'bg-purple-50',
      label: 'Volatile'
    },
    insufficient_data: {
      icon: '❓',
      color: 'text-gray-400',
      bg: 'bg-gray-50',
      label: 'Insufficient Data'
    },
  };
}

/**
 * Get anomaly severity colors
 */
export function useAnomalySeverityColors() {
  return {
    critical: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      border: 'border-red-300',
      badge: 'bg-red-500',
    },
    high: {
      bg: 'bg-orange-100',
      text: 'text-orange-800',
      border: 'border-orange-300',
      badge: 'bg-orange-500',
    },
    medium: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      border: 'border-yellow-300',
      badge: 'bg-yellow-500',
    },
    low: {
      bg: 'bg-blue-100',
      text: 'text-blue-800',
      border: 'border-blue-300',
      badge: 'bg-blue-500',
    },
  };
}
