import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { SemanticSearchResult } from '../types/analysis';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SearchParams {
  caseId: string;
  query: string;
  limit?: number;
  minScore?: number;
}

/**
 * Hook to perform semantic search on case documents
 */
export function useSemanticSearch() {
  return useMutation({
    mutationFn: async (params: SearchParams) => {
      const { caseId, query, limit = 10, minScore = 0.5 } = params;

      const response = await axios.post<SemanticSearchResult[]>(
        `${API_BASE_URL}/api/v1/analysis/search`,
        {
          case_id: caseId,
          query,
          limit,
          min_score: minScore
        }
      );

      return response.data;
    }
  });
}

/**
 * Hook to fetch saved searches for a case
 */
export function useSavedSearches(caseId: string | null) {
  return useQuery({
    queryKey: ['saved-searches', caseId],
    queryFn: async () => {
      if (!caseId) {
        throw new Error('Case ID is required');
      }

      const response = await axios.get<string[]>(
        `${API_BASE_URL}/api/cases/${caseId}/saved-searches`
      );

      return response.data;
    },
    enabled: !!caseId,
    staleTime: 5 * 60 * 1000 // 5 minutes
  });
}

/**
 * Hook to save a search query
 */
export function useSaveSearch() {
  return useMutation({
    mutationFn: async (params: { caseId: string; query: string }) => {
      const { caseId, query } = params;

      const response = await axios.post(
        `${API_BASE_URL}/api/cases/${caseId}/saved-searches`,
        { query }
      );

      return response.data;
    }
  });
}

/**
 * Example search queries (Polish)
 */
export const EXAMPLE_QUERIES = [
  'Jaki jest trend wzrostu przychodów?',
  'Jak zmieniało się zadłużenie w czasie?',
  'Jakie są główne wydatki?',
  'Opisz sytuację przepływów pieniężnych',
  'Jakie są kluczowe ryzyka finansowe?',
  'Podsumuj pozycję płynnościową'
];
