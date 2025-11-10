/**
 * Cases API Service
 * All case management operations (CRUD, stats)
 */

import { api } from '@/lib/api';
import type {
  Case,
  CaseCreate,
  CaseUpdate,
  CaseStats,
  CaseListParams,
  PaginatedResponse,
} from '@/types/api';

/**
 * Cases API operations
 */
export const casesApi = {
  /**
   * List cases with pagination and filtering
   * GET /api/cases/
   *
   * @example
   * ```ts
   * const result = await casesApi.list({ page: 1, page_size: 20, status: 'active' });
   * console.log(result.cases, result.total, result.total_pages);
   * ```
   */
  list: async (params?: CaseListParams): Promise<PaginatedResponse<Case>> => {
    const { data } = await api.get<PaginatedResponse<Case>>('/cases/', { params });
    return data;
  },

  /**
   * Create new case
   * POST /api/cases/
   *
   * @example
   * ```ts
   * const newCase = await casesApi.create({
   *   name: 'Financial Fraud Investigation 2024-Q1',
   *   description: 'Investigation into suspected financial irregularities'
   * });
   * console.log('Created case:', newCase.id);
   * ```
   */
  create: async (caseData: CaseCreate): Promise<Case> => {
    const { data } = await api.post<Case>('/cases/', caseData);
    return data;
  },

  /**
   * Get case by ID
   * GET /api/cases/{case_id}
   *
   * @example
   * ```ts
   * const case = await casesApi.get('550e8400-e29b-41d4-a716-446655440000');
   * console.log('Case:', case.name, 'Documents:', case.document_count);
   * ```
   */
  get: async (caseId: string): Promise<Case> => {
    const { data } = await api.get<Case>(`/cases/${caseId}`);
    return data;
  },

  /**
   * Update case
   * PATCH /api/cases/{case_id}
   *
   * @example
   * ```ts
   * const updated = await casesApi.update('550e8400-e29b-41d4-a716-446655440000', {
   *   name: 'Updated Case Name',
   *   status: 'completed'
   * });
   * ```
   */
  update: async (caseId: string, updates: CaseUpdate): Promise<Case> => {
    const { data } = await api.patch<Case>(`/cases/${caseId}`, updates);
    return data;
  },

  /**
   * Delete case (soft delete - sets status to archived)
   * DELETE /api/cases/{case_id}
   *
   * @example
   * ```ts
   * await casesApi.delete('550e8400-e29b-41d4-a716-446655440000');
   * console.log('Case archived');
   * ```
   */
  delete: async (caseId: string): Promise<void> => {
    await api.delete(`/cases/${caseId}`);
  },

  /**
   * Get case processing statistics
   * GET /api/cases/{case_id}/stats
   *
   * @example
   * ```ts
   * const stats = await casesApi.getStats('550e8400-e29b-41d4-a716-446655440000');
   * console.log('Total documents:', stats.total_documents);
   * console.log('Completed:', stats.completed, 'Failed:', stats.failed);
   * console.log('Success rate:', stats.success_rate + '%');
   * ```
   */
  getStats: async (caseId: string): Promise<CaseStats> => {
    const { data } = await api.get<CaseStats>(`/cases/${caseId}/stats`);
    return data;
  },
};
