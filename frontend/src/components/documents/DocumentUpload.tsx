/**
 * DocumentUpload Component
 *
 * Main upload component with drag-and-drop, validation, and upload queue
 * - Drag and drop zone using react-dropzone
 * - File validation (PDF only, max 500MB)
 * - Multiple file support
 * - Upload queue with progress tracking
 * - Cancel upload capability
 * - Integration with useUploadDocument() hook
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { validateFiles, getDuplicateFilenames } from '../../lib/fileValidation';
import { DropZone, FilePreview } from './DropZone';
import { UploadProgress, type FileUploadProgress } from './UploadProgress';
import { useUploadDocument } from '../../hooks/useDocuments';

interface DocumentUploadProps {
  caseId: string;
  onUploadComplete?: (documentId: string) => void;
  onUploadError?: (error: Error) => void;
  className?: string;
  autoRedirect?: boolean; // Redirect to document status page after upload
}

export function DocumentUpload({
  caseId,
  onUploadComplete,
  onUploadError,
  className,
  autoRedirect = true,
}: DocumentUploadProps) {
  const navigate = useNavigate();
  const uploadMutation = useUploadDocument();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploads, setUploads] = useState<FileUploadProgress[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Handle file selection
  const handleFilesSelected = useCallback((newFiles: File[]) => {
    setUploadError(null);

    // Validate files
    const validationResults = validateFiles(newFiles);
    const validFiles = validationResults
      .filter((r) => r.validation.valid)
      .map((r) => r.file);

    // Check for errors
    const invalidFiles = validationResults.filter((r) => !r.validation.valid);
    if (invalidFiles.length > 0) {
      const errors = invalidFiles
        .map((r) => `${r.file.name}: ${r.validation.error}`)
        .join('\n');
      setUploadError(errors);
      return;
    }

    // Check for duplicates with existing files
    const allFiles = [...selectedFiles, ...validFiles];
    const duplicates = getDuplicateFilenames(allFiles);
    if (duplicates.length > 0) {
      setUploadError(`Duplicate files detected: ${duplicates.join(', ')}`);
      return;
    }

    // Add valid files to selection
    setSelectedFiles((prev) => [...prev, ...validFiles]);
  }, [selectedFiles]);

  // Remove file from selection
  const handleRemoveFile = useCallback((file: File) => {
    setSelectedFiles((prev) => prev.filter((f) => f !== file));
  }, []);

  // Start upload
  const handleStartUpload = useCallback(async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadError(null);

    // Initialize upload progress for all files
    const initialUploads: FileUploadProgress[] = selectedFiles.map((file) => ({
      file,
      progress: 0,
      uploadedBytes: 0,
      totalBytes: file.size,
      status: 'uploading',
    }));
    setUploads(initialUploads);

    try {
      // Upload files sequentially
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];

        try {
          // Real API upload with progress tracking
          const response = await uploadMutation.mutateAsync({
            caseId,
            file,
            onProgress: (progressData) => {
              setUploads((prev) =>
                prev.map((upload, index) =>
                  index === i
                    ? {
                        ...upload,
                        progress: progressData.percentage,
                        uploadedBytes: progressData.loaded,
                        speed: 0, // Speed calculation can be added if needed
                      }
                    : upload
                )
              );
            },
          });

          // Mark as completed
          setUploads((prev) =>
            prev.map((upload, index) =>
              index === i
                ? {
                    ...upload,
                    status: 'completed',
                    progress: 100,
                    uploadedBytes: file.size,
                  }
                : upload
            )
          );

          // Callback on complete
          if (onUploadComplete) {
            onUploadComplete(response.document_id);
          }

          // Auto-redirect to document status page (only for first file)
          if (autoRedirect && i === 0) {
            navigate(`/cases/${caseId}/documents/${response.document_id}`);
          }
        } catch (error) {
          // Mark as error
          setUploads((prev) =>
            prev.map((upload, index) =>
              index === i
                ? {
                    ...upload,
                    status: 'error',
                    error: error instanceof Error ? error.message : 'Upload failed',
                  }
                : upload
            )
          );

          if (onUploadError && error instanceof Error) {
            onUploadError(error);
          }
        }
      }
    } finally {
      setIsUploading(false);
    }
  }, [selectedFiles, caseId, uploadMutation, onUploadComplete, onUploadError, autoRedirect, navigate]);

  // Cancel upload
  const handleCancelUpload = useCallback((file: File) => {
    setUploads((prev) =>
      prev.map((upload) =>
        upload.file === file && upload.status === 'uploading'
          ? { ...upload, status: 'cancelled' }
          : upload
      )
    );
  }, []);

  // Clear completed/error uploads
  const handleClearUploads = useCallback(() => {
    setUploads([]);
    setSelectedFiles([]);
    setUploadError(null);
  }, []);

  return (
    <div className={cn('space-y-6', className)}>
      {/* Upload error */}
      {uploadError && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200">
          <div className="flex gap-3">
            <svg
              className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-900">Upload Error</p>
              <p className="text-sm text-red-700 mt-1 whitespace-pre-line">{uploadError}</p>
            </div>
            <button
              onClick={() => setUploadError(null)}
              className="text-red-600 hover:text-red-800"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Drop zone */}
      <DropZone
        onFilesSelected={handleFilesSelected}
        disabled={isUploading}
        multiple={true}
      />

      {/* File preview */}
      {selectedFiles.length > 0 && uploads.length === 0 && (
        <FilePreview files={selectedFiles} onRemove={handleRemoveFile} />
      )}

      {/* Upload button */}
      {selectedFiles.length > 0 && !isUploading && uploads.length === 0 && (
        <div className="flex items-center justify-end gap-3">
          <button
            onClick={handleClearUploads}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Clear All
          </button>
          <button
            onClick={handleStartUpload}
            className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            Upload {selectedFiles.length} {selectedFiles.length === 1 ? 'File' : 'Files'}
          </button>
        </div>
      )}

      {/* Upload progress */}
      {uploads.length > 0 && (
        <UploadProgress uploads={uploads} onCancel={isUploading ? handleCancelUpload : undefined} />
      )}

      {/* Clear button after upload */}
      {uploads.length > 0 && !isUploading && (
        <div className="flex justify-end">
          <button
            onClick={handleClearUploads}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
}
