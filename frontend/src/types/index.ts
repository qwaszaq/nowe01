/**
 * Type definitions for the Investigation Intelligence Platform
 */

// ============================================================================
// ENUMS
// ============================================================================

export enum CaseStatus {
  OPEN = 'open',
  IN_PROGRESS = 'in_progress',
  UNDER_REVIEW = 'under_review',
  COMPLETED = 'completed',
  ARCHIVED = 'archived',
  CLOSED = 'closed'
}

export enum DocumentStatus {
  PENDING = 'pending',
  VALIDATING = 'validating',
  EXTRACTING = 'extracting',
  CHUNKING = 'chunking',
  EMBEDDING = 'embedding',
  STORING = 'storing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum AnalysisStatus {
  QUEUED = 'queued',
  SEARCHING = 'searching',
  CALCULATING = 'calculating',
  CLASSIFYING = 'classifying',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

// ============================================================================
// BASE TYPES
// ============================================================================

export interface TimestampedModel {
  created_at: string;
  updated_at: string;
}

export interface IdentifiedModel extends TimestampedModel {
  id: string;
}

// ============================================================================
// CASE TYPES
// ============================================================================

export interface Case extends IdentifiedModel {
  name: string;
  description?: string;
  status: CaseStatus;
  document_count?: number;
  analysis_count?: number;
}

export interface CreateCaseRequest {
  name: string;
  description?: string;
  status?: CaseStatus;
}

export interface UpdateCaseRequest {
  name?: string;
  description?: string;
  status?: CaseStatus;
}

export interface CaseStats {
  case_id: string;
  total_documents: number;
  documents_completed: number;
  documents_processing: number;
  documents_failed: number;
  total_chunks: number;
  total_analyses: number;
  success_rate: number;
  storage_size_mb: number;
}

// ============================================================================
// DOCUMENT TYPES
// ============================================================================

export interface Document extends IdentifiedModel {
  case_id: string;
  filename: string;
  original_filename: string;
  status: DocumentStatus;
  file_size: number;
  mime_type: string;
  page_count?: number;
  chunk_count?: number;
  processing_started_at?: string;
  processing_completed_at?: string;
  error_message?: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  status: DocumentStatus;
  message: string;
}

export interface ProcessingStatus {
  document_id: string;
  state: DocumentStatus;
  progress_percent: number;
  current_stage: string;
  error_details?: string;
  started_at: string;
  updated_at: string;
}

// ============================================================================
// ANALYSIS TYPES
// ============================================================================

export interface AnalysisResult extends IdentifiedModel {
  case_id: string;
  document_id?: string;
  analysis_type: string;
  status: AnalysisStatus;
  query?: string;
  results: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface SemanticSearchRequest {
  case_id: string;
  query: string;
  top_k?: number;
  min_score?: number;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  content: string;
  score: number;
  metadata: {
    page_number?: number;
    chunk_index?: number;
    document_name?: string;
  };
}

export interface FinancialAnalysisRequest {
  case_id: string;
  analysis_type: 'comprehensive' | 'liquidity' | 'profitability' | 'leverage' | 'quick';
  document_ids?: string[];
}

export interface FinancialMetrics {
  liquidity?: Record<string, number>;
  profitability?: Record<string, number>;
  leverage?: Record<string, number>;
}

export interface FinancialInsights {
  classifications: Record<string, string>;
  risk_assessment?: string;
  recommendations?: string[];
}

// ============================================================================
// PAGINATION TYPES
// ============================================================================

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// FILTER TYPES
// ============================================================================

export interface CaseFilters extends PaginationParams {
  status?: CaseStatus;
  search?: string;
}

export interface DocumentFilters extends PaginationParams {
  case_id?: string;
  status?: DocumentStatus;
}

// ============================================================================
// ERROR TYPES
// ============================================================================

export interface ErrorResponse {
  error: string;
  detail?: string;
  error_code?: string;
  timestamp: string;
}

export interface ValidationError {
  loc: string[];
  msg: string;
  type: string;
}

export interface ValidationErrorResponse {
  error: string;
  errors: ValidationError[];
  timestamp: string;
}

// ============================================================================
// UI TYPES
// ============================================================================

export type ViewMode = 'grid' | 'table';

export interface ToastOptions {
  title: string;
  description?: string;
  variant?: 'default' | 'success' | 'error' | 'warning';
}
