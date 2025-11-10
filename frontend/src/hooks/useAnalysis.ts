/**
 * React Query Hooks for Analysis Operations
 * Custom hooks for financial analysis, semantic search, metrics, and insights
 */

import { useQuery, useMutation, useQueryClient, type UseQueryOptions } from '@tanstack/react-query';
import { analysisApi } from '@/services/api/analysisApi';
import type {
  AnalysisType,
  AnalysisResult,
  AnalysisRequest,
  SearchRequest,
  SearchResult,
  MetricsOnlyResponse,
  InsightsOnlyResponse,
} from '@/types/api';

// ============================================================================
// QUERY KEYS
// ============================================================================

/**
 * Query key factory for analysis operations
 */
export const analysisKeys = {
  all: ['analysis'] as const,
  results: () => [...analysisKeys.all, 'result'] as const,
  result: (documentId: string, analysisType: AnalysisType) =>
    [...analysisKeys.results(), documentId, analysisType] as const,
  metrics: (documentId: string) => [...analysisKeys.all, 'metrics', documentId] as const,
  insights: (documentId: string) => [...analysisKeys.all, 'insights', documentId] as const,
  searches: () => [...analysisKeys.all, 'search'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * Get cached analysis results (does not trigger new analysis)
 *
 * @example
 * ```tsx
 * function AnalysisResults({ documentId }: { documentId: string }) {
 *   const { data, isLoading, error } = useAnalysisResult(documentId, 'comprehensive');
 *
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>No cached results. Run analysis first.</div>;
 *
 *   return (
 *     <div>
 *       <h2>Quality Score: {data.quality_score}%</h2>
 *       <h3>Metrics ({data.metrics.length})</h3>
 *       {data.metrics.map(m => (
 *         <div key={m.metric_name}>
 *           {m.metric_name}: {m.metric_value} {m.metric_unit}
 *         </div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useAnalysisResult(
  documentId: string,
  analysisType: AnalysisType = 'comprehensive',
  options?: Omit<UseQueryOptions<AnalysisResult>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AnalysisResult>({
    queryKey: analysisKeys.result(documentId, analysisType),
    queryFn: () => analysisApi.getCached(documentId, analysisType),
    enabled: !!documentId,
    staleTime: 1000 * 60 * 60, // 1 hour (results are cached server-side)
    retry: false, // Don't retry if no cached result exists
    ...options,
  });
}

/**
 * Get document metrics only
 */
export function useMetrics(
  documentId: string,
  metricNames?: string[],
  options?: Omit<UseQueryOptions<MetricsOnlyResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery<MetricsOnlyResponse>({
    queryKey: analysisKeys.metrics(documentId),
    queryFn: () => analysisApi.getMetrics(documentId, metricNames),
    enabled: !!documentId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

/**
 * Get document insights only
 */
export function useInsights(
  documentId: string,
  options?: Omit<UseQueryOptions<InsightsOnlyResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery<InsightsOnlyResponse>({
    queryKey: analysisKeys.insights(documentId),
    queryFn: () => analysisApi.getInsights(documentId),
    enabled: !!documentId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/**
 * Run financial analysis mutation
 *
 * @example
 * ```tsx
 * function RunAnalysisButton({ documentId }: { documentId: string }) {
 *   const runAnalysis = useRunAnalysis();
 *
 *   const handleAnalysis = async () => {
 *     try {
 *       const result = await runAnalysis.mutateAsync({
 *         document_id: documentId,
 *         analysis_type: 'comprehensive',
 *       });
 *
 *       console.log('Analysis complete!');
 *       console.log('Quality:', result.quality_score);
 *       console.log('Cached:', result.cached);
 *       console.log('Time:', result.execution_time_ms + 'ms');
 *     } catch (error) {
 *       console.error('Analysis failed:', error);
 *     }
 *   };
 *
 *   return (
 *     <button onClick={handleAnalysis} disabled={runAnalysis.isPending}>
 *       {runAnalysis.isPending ? 'Analyzing...' : 'Run Analysis'}
 *     </button>
 *   );
 * }
 * ```
 */
export function useRunAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AnalysisRequest) => analysisApi.analyze(request),
    onSuccess: (data) => {
      // Update the cache with new results
      queryClient.setQueryData(
        analysisKeys.result(data.document_id, data.analysis_type as AnalysisType),
        data
      );

      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: analysisKeys.metrics(data.document_id),
      });
      queryClient.invalidateQueries({
        queryKey: analysisKeys.insights(data.document_id),
      });
    },
  });
}

/**
 * Semantic search mutation
 *
 * @example
 * ```tsx
 * function SemanticSearch({ caseId }: { caseId: string }) {
 *   const [query, setQuery] = useState('');
 *   const search = useSemanticSearch();
 *
 *   const handleSearch = async () => {
 *     try {
 *       const results = await search.mutateAsync({
 *         case_id: caseId,
 *         query,
 *         limit: 10,
 *         context_window: 2,
 *       });
 *
 *       console.log(`Found ${results.length} results`);
 *       results.forEach(r => {
 *         console.log(`Score: ${r.score}, Page: ${r.page_num}`);
 *         console.log(r.text);
 *       });
 *     } catch (error) {
 *       console.error('Search failed:', error);
 *     }
 *   };
 *
 *   return (
 *     <div>
 *       <input
 *         value={query}
 *         onChange={(e) => setQuery(e.target.value)}
 *         placeholder="Search documents..."
 *       />
 *       <button onClick={handleSearch} disabled={search.isPending}>
 *         Search
 *       </button>
 *
 *       {search.data && (
 *         <div>
 *           {search.data.map(result => (
 *             <div key={result.chunk_id}>
 *               <p>Score: {result.score.toFixed(2)}</p>
 *               <p>{result.text}</p>
 *             </div>
 *           ))}
 *         </div>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useSemanticSearch() {
  return useMutation({
    mutationFn: (request: SearchRequest) => analysisApi.search(request),
  });
}
