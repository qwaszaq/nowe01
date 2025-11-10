/**
 * Cases API
 * CRUD operations for case management
 */

import { apiClient } from './client';
import type {
  Case,
  CreateCaseRequest,
  UpdateCaseRequest,
  CaseStats,
  CaseFilters,
  PaginatedResponse,
} from '../types';

const CASES_ENDPOINT = '/cases';

/**
 * Get paginated list of cases with optional filters
 */
export async function getCases(filters?: CaseFilters): Promise<PaginatedResponse<Case>> {
  const params = new URLSearchParams();

  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());
  if (filters?.status) params.append('status', filters.status);
  if (filters?.search) params.append('search', filters.search);

  const { data } = await apiClient.get<PaginatedResponse<Case>>(
    `${CASES_ENDPOINT}?${params.toString()}`
  );

  return data;
}

/**
 * Get a single case by ID
 */
export async function getCase(caseId: string): Promise<Case> {
  const { data } = await apiClient.get<Case>(`${CASES_ENDPOINT}/${caseId}`);
  return data;
}

/**
 * Create a new case
 */
export async function createCase(request: CreateCaseRequest): Promise<Case> {
  const { data } = await apiClient.post<Case>(CASES_ENDPOINT, request);
  return data;
}

/**
 * Update an existing case
 */
export async function updateCase(caseId: string, request: UpdateCaseRequest): Promise<Case> {
  const { data } = await apiClient.put<Case>(`${CASES_ENDPOINT}/${caseId}`, request);
  return data;
}

/**
 * Delete a case
 */
export async function deleteCase(caseId: string): Promise<void> {
  await apiClient.delete(`${CASES_ENDPOINT}/${caseId}`);
}

/**
 * Get case statistics
 */
export async function getCaseStats(caseId: string): Promise<CaseStats> {
  const { data } = await apiClient.get<CaseStats>(`${CASES_ENDPOINT}/${caseId}/stats`);
  return data;
}

/**
 * Get dashboard statistics (all cases summary)
 */
export async function getDashboardStats(): Promise<{
  total_cases: number;
  active_cases: number;
  total_documents: number;
  documents_processed: number;
  total_analyses: number;
}> {
  const { data } = await apiClient.get(`${CASES_ENDPOINT}/stats/dashboard`);
  return data;
}
