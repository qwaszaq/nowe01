/**
 * React Query Hooks for Document Management
 * Custom hooks for document upload, listing, status tracking with automatic polling
 */

import { useQuery, useMutation, useQueryClient, type UseQueryOptions } from '@tanstack/react-query';
import { documentsApi } from '@/services/api/documentsApi';
import type {
  Document,
  DocumentUploadResponse,
  DocumentStatusResponse,
  DocumentListParams,
  PaginatedResponse,
  OnUploadProgress,
  DocumentStatus,
} from '@/types/api';
import { useState, useCallback } from 'react';

// ============================================================================
// QUERY KEYS
// ============================================================================

/**
 * Query key factory for documents
 */
export const documentKeys = {
  all: ['documents'] as const,
  lists: () => [...documentKeys.all, 'list'] as const,
  list: (filters?: DocumentListParams) => [...documentKeys.lists(), filters] as const,
  details: () => [...documentKeys.all, 'detail'] as const,
  detail: (id: string) => [...documentKeys.details(), id] as const,
  status: (id: string) => [...documentKeys.detail(id), 'status'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * List documents with filtering and pagination
 *
 * @example
 * ```tsx
 * function DocumentsList({ caseId }: { caseId: string }) {
 *   const { data, isLoading } = useDocuments({ case_id: caseId, page: 1 });
 *
 *   return (
 *     <div>
 *       <h2>Documents ({data.total})</h2>
 *       {data.documents?.map(doc => (
 *         <div key={doc.id}>
 *           <h3>{doc.original_filename}</h3>
 *           <span>Status: {doc.status}</span>
 *           <span>Pages: {doc.page_count}</span>
 *         </div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useDocuments(
  params?: DocumentListParams,
  options?: Omit<UseQueryOptions<PaginatedResponse<Document>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PaginatedResponse<Document>>({
    queryKey: documentKeys.list(params),
    queryFn: () => documentsApi.list(params),
    staleTime: 1000 * 30, // 30 seconds
    ...options,
  });
}

/**
 * Get single document by ID
 *
 * @example
 * ```tsx
 * function DocumentDetail({ documentId }: { documentId: string }) {
 *   const { data: doc, isLoading } = useDocument(documentId);
 *
 *   if (isLoading) return <div>Loading...</div>;
 *
 *   return (
 *     <div>
 *       <h1>{doc.original_filename}</h1>
 *       <p>Size: {(doc.file_size / 1024 / 1024).toFixed(2)} MB</p>
 *       <p>Status: {doc.status}</p>
 *       <p>Pages: {doc.page_count}</p>
 *       <p>Chunks: {doc.chunk_count}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useDocument(
  documentId: string,
  options?: Omit<UseQueryOptions<Document>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Document>({
    queryKey: documentKeys.detail(documentId),
    queryFn: () => documentsApi.get(documentId),
    enabled: !!documentId,
    staleTime: 1000 * 60, // 1 minute
    ...options,
  });
}

/**
 * Get document processing status with automatic polling
 *
 * Automatically polls every 2 seconds while document is processing.
 * Stops polling when status is 'completed' or 'failed'.
 *
 * @example
 * ```tsx
 * function DocumentStatus({ documentId }: { documentId: string }) {
 *   const { data: status } = useDocumentStatus(documentId);
 *
 *   return (
 *     <div>
 *       <h3>Processing Status</h3>
 *       <div>State: {status.state}</div>
 *       <div>Progress: {status.progress_percent}%</div>
 *       <div>Stage: {status.current_stage}</div>
 *       {status.error_details && (
 *         <div className="error">Error: {status.error_details}</div>
 *       )}
 *       <ProgressBar value={status.progress_percent} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useDocumentStatus(
  documentId: string,
  options?: Omit<UseQueryOptions<DocumentStatusResponse>, 'queryKey' | 'queryFn' | 'refetchInterval'>
) {
  return useQuery<DocumentStatusResponse>({
    queryKey: documentKeys.status(documentId),
    queryFn: () => documentsApi.getStatus(documentId),
    enabled: !!documentId,
    refetchInterval: (data) => {
      // Poll every 2 seconds while processing
      if (!data) return 2000;

      const processingStates: DocumentStatus[] = [
        'pending' as DocumentStatus,
        'processing' as DocumentStatus,
        'extracting' as DocumentStatus,
        'chunking' as DocumentStatus,
        'embedding' as DocumentStatus,
        'storing' as DocumentStatus,
      ];

      const isProcessing = processingStates.includes(data.state as DocumentStatus);
      return isProcessing ? 2000 : false; // Poll every 2s or stop
    },
    ...options,
  });
}

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/**
 * Upload document with progress tracking
 *
 * @example
 * ```tsx
 * function DocumentUpload({ caseId }: { caseId: string }) {
 *   const [progress, setProgress] = useState(0);
 *   const uploadDocument = useUploadDocument();
 *
 *   const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
 *     const file = e.target.files?.[0];
 *     if (!file) return;
 *
 *     try {
 *       const result = await uploadDocument.mutateAsync({
 *         caseId,
 *         file,
 *         onProgress: (p) => setProgress(p.percentage),
 *       });
 *
 *       console.log('Document uploaded:', result.document_id);
 *       // Navigate to document status page or start polling
 *     } catch (error) {
 *       console.error('Upload failed:', error);
 *     }
 *   };
 *
 *   return (
 *     <div>
 *       <input type="file" accept=".pdf" onChange={handleFileChange} />
 *       {uploadDocument.isPending && (
 *         <div>
 *           <div>Uploading: {progress}%</div>
 *           <ProgressBar value={progress} />
 *         </div>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      caseId,
      file,
      onProgress,
    }: {
      caseId: string;
      file: File;
      onProgress?: OnUploadProgress;
    }) => {
      return documentsApi.upload(caseId, file, onProgress);
    },
    onSuccess: () => {
      // Invalidate document lists to refetch
      queryClient.invalidateQueries({ queryKey: documentKeys.lists() });
    },
  });
}

/**
 * Delete document mutation
 *
 * @example
 * ```tsx
 * function DeleteDocumentButton({ documentId }: { documentId: string }) {
 *   const deleteDocument = useDeleteDocument();
 *
 *   const handleDelete = async () => {
 *     if (!confirm('Delete this document? This action cannot be undone.')) return;
 *
 *     try {
 *       await deleteDocument.mutateAsync(documentId);
 *       toast.success('Document deleted');
 *       navigate('/documents');
 *     } catch (error) {
 *       toast.error('Failed to delete document');
 *     }
 *   };
 *
 *   return (
 *     <button
 *       onClick={handleDelete}
 *       disabled={deleteDocument.isPending}
 *     >
 *       {deleteDocument.isPending ? 'Deleting...' : 'Delete'}
 *     </button>
 *   );
 * }
 * ```
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => documentsApi.delete(documentId),
    onSuccess: (_, deletedDocumentId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: documentKeys.detail(deletedDocumentId) });
      queryClient.removeQueries({ queryKey: documentKeys.status(deletedDocumentId) });

      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: documentKeys.lists() });
    },
  });
}

/**
 * Reprocess failed document mutation
 *
 * @example
 * ```tsx
 * function ReprocessButton({ documentId }: { documentId: string }) {
 *   const reprocess = useReprocessDocument();
 *
 *   const handleReprocess = async () => {
 *     try {
 *       await reprocess.mutateAsync(documentId);
 *       toast.success('Reprocessing started');
 *     } catch (error) {
 *       toast.error('Failed to start reprocessing');
 *     }
 *   };
 *
 *   return (
 *     <button onClick={handleReprocess} disabled={reprocess.isPending}>
 *       Retry Processing
 *     </button>
 *   );
 * }
 * ```
 */
export function useReprocessDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => documentsApi.reprocess(documentId),
    onSuccess: (_, documentId) => {
      // Invalidate status to start polling again
      queryClient.invalidateQueries({ queryKey: documentKeys.status(documentId) });
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(documentId) });
    },
  });
}

// ============================================================================
// COMPOSITE HOOKS
// ============================================================================

/**
 * Combined hook for document upload with automatic status tracking
 *
 * Returns upload function and current status of the uploaded document.
 * Automatically starts polling status after successful upload.
 *
 * @example
 * ```tsx
 * function SmartDocumentUpload({ caseId }: { caseId: string }) {
 *   const {
 *     upload,
 *     uploadProgress,
 *     isUploading,
 *     uploadedDocumentId,
 *     processingStatus,
 *   } = useDocumentUploadWithStatus(caseId);
 *
 *   return (
 *     <div>
 *       <input
 *         type="file"
 *         accept=".pdf"
 *         onChange={(e) => {
 *           const file = e.target.files?.[0];
 *           if (file) upload(file);
 *         }}
 *       />
 *
 *       {isUploading && <div>Uploading: {uploadProgress}%</div>}
 *
 *       {uploadedDocumentId && processingStatus && (
 *         <div>
 *           <h3>Processing Document</h3>
 *           <div>Status: {processingStatus.state}</div>
 *           <div>Progress: {processingStatus.progress_percent}%</div>
 *         </div>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useDocumentUploadWithStatus(caseId: string) {
  const [uploadedDocumentId, setUploadedDocumentId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const uploadMutation = useUploadDocument();
  const statusQuery = useDocumentStatus(uploadedDocumentId || '', {
    enabled: !!uploadedDocumentId,
  });

  const upload = useCallback(
    async (file: File) => {
      try {
        const result = await uploadMutation.mutateAsync({
          caseId,
          file,
          onProgress: (progress) => setUploadProgress(progress.percentage),
        });

        setUploadedDocumentId(result.document_id);
        return result;
      } catch (error) {
        setUploadProgress(0);
        throw error;
      }
    },
    [caseId, uploadMutation]
  );

  return {
    upload,
    uploadProgress,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,
    uploadedDocumentId,
    processingStatus: statusQuery.data,
    isProcessing: statusQuery.isLoading || (statusQuery.data?.state !== 'completed' && statusQuery.data?.state !== 'failed'),
    reset: () => {
      setUploadedDocumentId(null);
      setUploadProgress(0);
      uploadMutation.reset();
    },
  };
}
