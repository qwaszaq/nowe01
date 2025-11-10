/**
 * TypeScript Types for Investigation Intelligence Platform API
 * Complete type definitions for all backend endpoints and responses
 */

// ============================================================================
// ENUMS
// ============================================================================

export enum DocumentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  EXTRACTING = 'extracting',
  CHUNKING = 'chunking',
  EMBEDDING = 'embedding',
  STORING = 'storing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum CaseStatus {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  ARCHIVED = 'archived',
}

export type AnalysisType = 'comprehensive' | 'liquidity' | 'profitability' | 'leverage' | 'quick';

// ============================================================================
// BASE TYPES
// ============================================================================

export interface PaginatedResponse<T> {
  items?: T[]; // for generic pagination
  cases?: T[]; // for cases endpoint
  documents?: T[]; // for documents endpoint
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
  error_code?: string;
  timestamp?: string;
}

// ============================================================================
// CASE TYPES
// ============================================================================

export interface Case {
  id: string;
  name: string;
  description?: string;
  status: CaseStatus;
  created_at: string;
  updated_at: string;
  document_count: number;
}

export interface CaseCreate {
  name: string;
  description?: string;
}

export interface CaseUpdate {
  name?: string;
  description?: string;
  status?: CaseStatus;
}

export interface CaseStats {
  case_id: string;
  total_documents: number;
  pending: number;
  extracting: number;
  chunking: number;
  embedding: number;
  storing: number;
  completed: number;
  failed: number;
  success_rate: number;
  error_rate: number;
  avg_processing_time_seconds?: number;
  errors_by_type: Record<string, number>;
}

// ============================================================================
// DOCUMENT TYPES
// ============================================================================

export interface Document {
  id: string;
  case_id: string;
  filename: string;
  original_filename: string;
  status: DocumentStatus;
  file_size: number;
  mime_type: string;
  page_count?: number;
  chunk_count?: number;
  created_at: string;
  processing_started_at?: string;
  processing_completed_at?: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  status: string;
  message: string;
}

export interface DocumentStatusResponse {
  document_id: string;
  state: string;
  progress_percent: number;
  current_stage: string;
  error_details?: string;
  started_at?: string;
  updated_at?: string;
}

export interface DocumentListParams {
  case_id?: string;
  status?: DocumentStatus;
  page?: number;
  page_size?: number;
}

// ============================================================================
// ANALYSIS TYPES
// ============================================================================

export interface MetricCitation {
  page_numbers?: number[];
  formula?: string;
  page_number?: number;
  calculation_method?: string;
}

export interface FinancialMetric {
  metric_name: string;
  metric_value?: number;
  metric_unit?: string;
  interpretation: string;
  category: 'liquidity' | 'profitability' | 'leverage' | 'unknown';
  citations: MetricCitation[];
}

export interface AnalysisInsights {
  risk_assessment: string;
  liquidity_position: string;
  profitability_trends: string;
  leverage_analysis: string;
  overall_health: string;
  key_concerns: string[];
  key_strengths: string[];
  classification_count: number;
}

export interface AnalysisResult {
  document_id: string;
  analysis_type: AnalysisType;
  quality_score: number;
  metrics: FinancialMetric[];
  insights: AnalysisInsights;
  cached: boolean;
  execution_time_ms: number;
  timestamp: string;
}

export interface AnalysisRequest {
  document_id: string;
  analysis_type: AnalysisType;
}

export interface MetricsOnlyResponse {
  document_id: string;
  metrics: FinancialMetric[];
  total_count: number;
  timestamp: string;
}

export interface InsightsOnlyResponse {
  document_id: string;
  insights: AnalysisInsights;
  timestamp: string;
}

// ============================================================================
// SEARCH TYPES
// ============================================================================

export interface SearchContextChunk {
  text: string;
  page_num?: number;
  chunk_id?: string;
}

export interface SearchContext {
  before?: SearchContextChunk[];
  after?: SearchContextChunk[];
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  page_num: number;
  text: string;
  score: number;
  context?: SearchContext;
}

export interface SearchRequest {
  case_id?: string;
  document_id?: string;
  query: string;
  limit?: number;
  context_window?: number;
}

// ============================================================================
// QUERY PARAMETERS
// ============================================================================

export interface CaseListParams {
  page?: number;
  page_size?: number;
  status?: CaseStatus;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

// ============================================================================
// API CLIENT TYPES
// ============================================================================

export interface ApiError extends Error {
  status?: number;
  code?: string;
  detail?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export type OnUploadProgress = (progress: UploadProgress) => void;
