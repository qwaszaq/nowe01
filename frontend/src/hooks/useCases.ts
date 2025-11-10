/**
 * React Query Hooks for Case Management
 * Custom hooks for case CRUD operations with automatic caching and invalidation
 */

import { useQuery, useMutation, useQueryClient, type UseQueryOptions } from '@tanstack/react-query';
import { casesApi } from '@/services/api/casesApi';
import type {
  Case,
  CaseCreate,
  CaseUpdate,
  CaseStats,
  CaseListParams,
  PaginatedResponse,
} from '@/types/api';

// ============================================================================
// QUERY KEYS
// ============================================================================

/**
 * Query key factory for cases
 * Provides type-safe, hierarchical query keys for React Query
 */
export const caseKeys = {
  all: ['cases'] as const,
  lists: () => [...caseKeys.all, 'list'] as const,
  list: (filters?: CaseListParams) => [...caseKeys.lists(), filters] as const,
  details: () => [...caseKeys.all, 'detail'] as const,
  detail: (id: string) => [...caseKeys.details(), id] as const,
  stats: (id: string) => [...caseKeys.detail(id), 'stats'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * List cases with pagination and filtering
 *
 * @example
 * ```tsx
 * function CasesList() {
 *   const { data, isLoading, error } = useCases({ page: 1, status: 'active' });
 *
 *   if (isLoading) return <div>Loading cases...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *
 *   return (
 *     <div>
 *       <h2>Total Cases: {data.total}</h2>
 *       {data.cases?.map(case => (
 *         <div key={case.id}>{case.name}</div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useCases(
  params?: CaseListParams,
  options?: Omit<UseQueryOptions<PaginatedResponse<Case>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PaginatedResponse<Case>>({
    queryKey: caseKeys.list(params),
    queryFn: () => casesApi.list(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    ...options,
  });
}

/**
 * Get single case by ID
 */
export function useCase(
  caseId: string,
  options?: Omit<UseQueryOptions<Case>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Case>({
    queryKey: caseKeys.detail(caseId),
    queryFn: () => casesApi.get(caseId),
    enabled: !!caseId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    ...options,
  });
}

/**
 * Get case processing statistics
 */
export function useCaseStats(
  caseId: string,
  options?: Omit<UseQueryOptions<CaseStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery<CaseStats>({
    queryKey: caseKeys.stats(caseId),
    queryFn: () => casesApi.getStats(caseId),
    enabled: !!caseId,
    staleTime: 1000 * 30, // 30 seconds
    ...options,
  });
}

/**
 * Get dashboard statistics (total cases, active cases, etc.)
 */
export function useDashboardStats(
  options?: Omit<UseQueryOptions<any>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      // Get all cases to calculate stats (max 100 per page due to API limit)
      const response = await casesApi.list({ page: 1, page_size: 100 });
      return {
        totalCases: response.total,
        activeCases: response.cases?.filter(c => c.status === 'active').length || 0,
        completedCases: response.cases?.filter(c => c.status === 'completed').length || 0,
        archivedCases: response.cases?.filter(c => c.status === 'archived').length || 0,
      };
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    ...options,
  });
}

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/**
 * Create new case mutation
 */
export function useCreateCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CaseCreate) => casesApi.create(data),
    onSuccess: (newCase) => {
      // Invalidate and refetch case lists
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });

      // Optimistically set the new case data
      queryClient.setQueryData(caseKeys.detail(newCase.id), newCase);
    },
  });
}

/**
 * Update case mutation
 */
export function useUpdateCase(caseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CaseUpdate) => casesApi.update(caseId, data),
    onMutate: async (updatedData) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: caseKeys.detail(caseId) });

      // Snapshot the previous value
      const previousCase = queryClient.getQueryData<Case>(caseKeys.detail(caseId));

      // Optimistically update to the new value
      if (previousCase) {
        queryClient.setQueryData<Case>(caseKeys.detail(caseId), {
          ...previousCase,
          ...updatedData,
          updated_at: new Date().toISOString(),
        });
      }

      // Return context with the previous value
      return { previousCase };
    },
    onError: (err, variables, context) => {
      // Rollback to previous value on error
      if (context?.previousCase) {
        queryClient.setQueryData(caseKeys.detail(caseId), context.previousCase);
      }
    },
    onSettled: () => {
      // Refetch to ensure we have the latest data
      queryClient.invalidateQueries({ queryKey: caseKeys.detail(caseId) });
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
    },
  });
}

/**
 * Delete case mutation (soft delete - archives the case)
 */
export function useDeleteCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (caseId: string) => casesApi.delete(caseId),
    onSuccess: (_, deletedCaseId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: caseKeys.detail(deletedCaseId) });

      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
    },
  });
}
