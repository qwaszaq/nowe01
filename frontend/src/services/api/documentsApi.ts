/**
 * Documents API Service
 * Document upload, management, and status tracking operations
 */

import { uploadApi, api } from '@/lib/api';
import type {
  Document,
  DocumentUploadResponse,
  DocumentStatusResponse,
  DocumentListParams,
  PaginatedResponse,
  OnUploadProgress,
} from '@/types/api';

/**
 * Documents API operations
 */
export const documentsApi = {
  /**
   * Upload document with progress tracking
   * POST /documents/upload
   *
   * @example
   * ```ts
   * const file = fileInput.files[0];
   * const result = await documentsApi.upload(
   *   '550e8400-e29b-41d4-a716-446655440000',
   *   file,
   *   (progress) => {
   *     console.log(`Upload progress: ${progress.percentage}%`);
   *   }
   * );
   * console.log('Document ID:', result.document_id);
   * ```
   */
  upload: async (
    caseId: string,
    file: File,
    onUploadProgress?: OnUploadProgress
  ): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append('case_id', caseId);
    formData.append('file', file);

    const { data } = await uploadApi.post<DocumentUploadResponse>(
      '/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onUploadProgress && progressEvent.total) {
            const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onUploadProgress({
              loaded: progressEvent.loaded,
              total: progressEvent.total,
              percentage,
            });
          }
        },
      }
    );

    return data;
  },

  /**
   * Get document processing status (for polling)
   * GET /documents/{document_id}/status
   *
   * @example
   * ```ts
   * const status = await documentsApi.getStatus('doc-uuid');
   * console.log('State:', status.state, 'Progress:', status.progress_percent + '%');
   * if (status.error_details) {
   *   console.error('Error:', status.error_details);
   * }
   * ```
   */
  getStatus: async (documentId: string): Promise<DocumentStatusResponse> => {
    const { data } = await api.get<DocumentStatusResponse>(`/documents/${documentId}/status`);
    return data;
  },

  /**
   * List documents with filtering and pagination
   * GET /documents/
   *
   * @example
   * ```ts
   * const result = await documentsApi.list({
   *   case_id: '550e8400-e29b-41d4-a716-446655440000',
   *   status: 'completed',
   *   page: 1,
   *   page_size: 20
   * });
   * console.log('Documents:', result.documents);
   * ```
   */
  list: async (params?: DocumentListParams): Promise<PaginatedResponse<Document>> => {
    const { data } = await api.get<PaginatedResponse<Document>>('/documents/', { params });
    return data;
  },

  /**
   * Get document by ID
   * GET /documents/{document_id}
   *
   * @example
   * ```ts
   * const doc = await documentsApi.get('doc-uuid');
   * console.log('Document:', doc.original_filename, 'Status:', doc.status);
   * console.log('Pages:', doc.page_count, 'Chunks:', doc.chunk_count);
   * ```
   */
  get: async (documentId: string): Promise<Document> => {
    const { data } = await api.get<Document>(`/documents/${documentId}`);
    return data;
  },

  /**
   * Delete document and all associated data
   * DELETE /documents/{document_id}
   *
   * @example
   * ```ts
   * await documentsApi.delete('doc-uuid');
   * console.log('Document deleted');
   * ```
   */
  delete: async (documentId: string): Promise<void> => {
    await api.delete(`/documents/${documentId}`);
  },

  /**
   * Reprocess failed document
   * POST /documents/{document_id}/reprocess
   *
   * @example
   * ```ts
   * const result = await documentsApi.reprocess('doc-uuid');
   * console.log('Reprocessing started:', result.message);
   * ```
   */
  reprocess: async (documentId: string): Promise<DocumentUploadResponse> => {
    const { data } = await api.post<DocumentUploadResponse>(
      `/documents/${documentId}/reprocess`
    );
    return data;
  },

  /**
   * Health check for documents API
   * GET /documents/health
   */
  healthCheck: async (): Promise<{ status: string; service: string }> => {
    const { data } = await api.get('/documents/health');
    return data;
  },
};
