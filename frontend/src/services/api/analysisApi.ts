/**
 * Analysis API Service
 * Financial analysis, semantic search, metrics, and insights operations
 */

import { api } from '@/lib/api';
import type {
  AnalysisRequest,
  AnalysisResult,
  AnalysisType,
  SearchRequest,
  SearchResult,
  MetricsOnlyResponse,
  InsightsOnlyResponse,
} from '@/types/api';

/**
 * Analysis API operations
 */
export const analysisApi = {
  /**
   * Run financial analysis on document
   * POST /api/analysis/analyze
   *
   * Supported analysis types:
   * - comprehensive: All 19 ratios + micro-agent insights
   * - liquidity: 5 liquidity ratios only
   * - profitability: 8 profitability ratios only
   * - leverage: 6 leverage ratios only
   * - quick: Key ratios only (current ratio, ROE, debt-to-equity)
   *
   * Results are automatically cached for 1 hour.
   *
   * @example
   * ```ts
   * const result = await analysisApi.analyze({
   *   document_id: '550e8400-e29b-41d4-a716-446655440000',
   *   analysis_type: 'comprehensive'
   * });
   *
   * console.log('Quality Score:', result.quality_score);
   * console.log('Metrics:', result.metrics.length);
   * console.log('Overall Health:', result.insights.overall_health);
   * console.log('Key Concerns:', result.insights.key_concerns);
   * console.log('Cached:', result.cached);
   * console.log('Execution Time:', result.execution_time_ms + 'ms');
   * ```
   */
  analyze: async (request: AnalysisRequest): Promise<AnalysisResult> => {
    const { data } = await api.post<AnalysisResult>('/analysis/analyze', request);
    return data;
  },

  /**
   * Get cached analysis results
   * GET /api/analysis/{document_id}
   *
   * Returns cached results if available, otherwise returns 404.
   * Use POST /analyze to generate new results.
   *
   * @example
   * ```ts
   * try {
   *   const cached = await analysisApi.getCached(
   *     '550e8400-e29b-41d4-a716-446655440000',
   *     'comprehensive'
   *   );
   *   console.log('Using cached results from:', cached.timestamp);
   * } catch (error) {
   *   console.log('No cached results, need to run analysis');
   * }
   * ```
   */
  getCached: async (
    documentId: string,
    analysisType: AnalysisType = 'comprehensive'
  ): Promise<AnalysisResult> => {
    const { data } = await api.get<AnalysisResult>(`/api/analysis/${documentId}`, {
      params: { analysis_type: analysisType },
    });
    return data;
  },

  /**
   * Semantic search across case or document
   * POST /api/analysis/search
   *
   * Provide either case_id (search all documents in case) or document_id (search single document).
   * Results are ranked by relevance with optional context windows.
   *
   * @example
   * ```ts
   * // Search across entire case
   * const results = await analysisApi.search({
   *   case_id: '550e8400-e29b-41d4-a716-446655440000',
   *   query: 'What is the company revenue growth?',
   *   limit: 10,
   *   context_window: 2
   * });
   *
   * results.forEach(result => {
   *   console.log(`Score: ${result.score.toFixed(2)}`);
   *   console.log(`Page: ${result.page_num}`);
   *   console.log(`Text: ${result.text}`);
   *   if (result.context) {
   *     console.log('Context before:', result.context.before);
   *     console.log('Context after:', result.context.after);
   *   }
   * });
   * ```
   */
  search: async (request: SearchRequest): Promise<SearchResult[]> => {
    const { data } = await api.post<SearchResult[]>('/analysis/search', request);
    return data;
  },

  /**
   * Get specific metrics for document
   * GET /api/analysis/{document_id}/metrics
   *
   * Returns all stored metrics from PostgreSQL. Optionally filter by metric names.
   *
   * @example
   * ```ts
   * // Get all metrics
   * const all = await analysisApi.getMetrics('doc-uuid');
   * console.log('Total metrics:', all.total_count);
   *
   * // Get specific metrics
   * const specific = await analysisApi.getMetrics('doc-uuid', ['current_ratio', 'roe']);
   * specific.metrics.forEach(m => {
   *   console.log(`${m.metric_name}: ${m.metric_value} ${m.metric_unit}`);
   * });
   * ```
   */
  getMetrics: async (
    documentId: string,
    metricNames?: string[]
  ): Promise<MetricsOnlyResponse> => {
    const params = metricNames ? { metric_names: metricNames.join(',') } : undefined;
    const { data } = await api.get<MetricsOnlyResponse>(
      `/api/analysis/${documentId}/metrics`,
      { params }
    );
    return data;
  },

  /**
   * Get AI insights for document
   * GET /api/analysis/{document_id}/insights
   *
   * Runs micro-agent classifiers on stored metrics to generate:
   * - Risk assessment
   * - Liquidity position
   * - Profitability trends
   * - Leverage analysis
   * - Overall health score
   * - Key concerns and strengths
   *
   * @example
   * ```ts
   * const insights = await analysisApi.getInsights('doc-uuid');
   *
   * console.log('Risk Assessment:', insights.insights.risk_assessment);
   * console.log('Liquidity Position:', insights.insights.liquidity_position);
   * console.log('Overall Health:', insights.insights.overall_health);
   * console.log('Key Concerns:', insights.insights.key_concerns);
   * console.log('Key Strengths:', insights.insights.key_strengths);
   * console.log('Classifications:', insights.insights.classification_count);
   * ```
   */
  getInsights: async (documentId: string): Promise<InsightsOnlyResponse> => {
    const { data } = await api.get<InsightsOnlyResponse>(
      `/api/analysis/${documentId}/insights`
    );
    return data;
  },

  /**
   * Health check for analysis API
   * GET /api/analysis/health
   */
  healthCheck: async (): Promise<{
    status: string;
    service: string;
    initialized: boolean;
    timestamp: string;
  }> => {
    const { data } = await api.get('/analysis/health');
    return data;
  },
};
