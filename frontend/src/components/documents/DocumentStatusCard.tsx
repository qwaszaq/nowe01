/**
 * DocumentStatusCard Component
 *
 * Real-time status display for a single document
 * - Shows filename, size, status badge
 * - Progress bar with percentage
 * - Current stage description
 * - Estimated time remaining
 * - Action buttons (Cancel, View Analysis, Retry)
 * - Automatically polls status while processing
 */

import { cn } from '../../lib/utils';
import { formatFileSize } from '../../lib/fileValidation';
import { formatRelativeTime } from '../../lib/utils';
import {
  DocumentStatusBadge,
  isProcessingStatus,
  isFinalStatus,
  getStatusProgress,
  getStageDescription,
  type DocumentStatus,
} from './DocumentStatusBadge';

export interface DocumentStatusData {
  document_id: string;
  filename: string;
  file_size: number;
  status: DocumentStatus;
  progress_percent?: number;
  current_stage?: string;
  chunks_processed?: number;
  total_chunks?: number;
  error_message?: string;
  uploaded_at?: Date | string;
  completed_at?: Date | string;
  estimated_time_remaining?: number; // in seconds
}

interface DocumentStatusCardProps {
  document: DocumentStatusData;
  onCancel?: (documentId: string) => void;
  onViewAnalysis?: (documentId: string) => void;
  onRetry?: (documentId: string) => void;
  className?: string;
}

export function DocumentStatusCard({
  document,
  onCancel,
  onViewAnalysis,
  onRetry,
  className,
}: DocumentStatusCardProps) {
  const {
    document_id,
    filename,
    file_size,
    status,
    progress_percent,
    current_stage,
    chunks_processed,
    total_chunks,
    error_message,
    uploaded_at,
    completed_at,
    estimated_time_remaining,
  } = document;

  const isProcessing = isProcessingStatus(status);
  const progress = progress_percent ?? getStatusProgress(status);
  const stageDescription = current_stage || getStageDescription(status);

  const formatEstimatedTime = (seconds: number): string => {
    if (seconds < 60) return `~${Math.ceil(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.ceil(seconds % 60);
    return `~${minutes}m ${secs}s`;
  };

  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 shadow-sm', className)}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            {/* Filename */}
            <h3 className="text-lg font-semibold text-gray-900 truncate" title={filename}>
              {filename}
            </h3>

            {/* File info */}
            <div className="mt-1 flex items-center gap-3 text-sm text-gray-600">
              <span>{formatFileSize(file_size)}</span>
              {uploaded_at && (
                <>
                  <span>•</span>
                  <span>Uploaded {formatRelativeTime(uploaded_at)}</span>
                </>
              )}
            </div>
          </div>

          {/* Status badge */}
          <DocumentStatusBadge status={status} />
        </div>
      </div>

      {/* Body */}
      <div className="p-6 space-y-6">
        {/* Processing state */}
        {isProcessing && (
          <>
            {/* Progress bar */}
            <div className="space-y-2">
              <div className="flex items-baseline justify-between">
                <p className="text-sm font-medium text-gray-700">{stageDescription}</p>
                <span className="text-sm font-medium text-gray-900">{progress}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Chunks progress (if available) */}
            {chunks_processed !== undefined && total_chunks !== undefined && (
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>Chunks processed</span>
                <span className="font-medium">
                  {chunks_processed} / {total_chunks}
                </span>
              </div>
            )}

            {/* Estimated time */}
            {estimated_time_remaining !== undefined && estimated_time_remaining > 0 && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>Estimated time remaining: {formatEstimatedTime(estimated_time_remaining)}</span>
              </div>
            )}

            {/* Animated processing indicator */}
            <div className="flex items-center gap-3 p-4 rounded-lg bg-blue-50 border border-blue-200">
              <svg
                className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <p className="text-sm text-blue-900">
                Processing document... This may take a few minutes.
              </p>
            </div>
          </>
        )}

        {/* Completed state */}
        {status === 'completed' && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 rounded-lg bg-green-50 border border-green-200">
              <svg
                className="w-6 h-6 text-green-600 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-900">Document ready for analysis</p>
                {completed_at && (
                  <p className="text-xs text-green-700 mt-1">
                    Completed {formatRelativeTime(completed_at)}
                  </p>
                )}
              </div>
            </div>

            {/* Metadata */}
            {total_chunks !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Total chunks</span>
                <span className="font-medium text-gray-900">{total_chunks}</span>
              </div>
            )}
          </div>
        )}

        {/* Failed state */}
        {status === 'failed' && (
          <div className="space-y-4">
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
                  <p className="text-sm font-medium text-red-900">Processing failed</p>
                  {error_message && (
                    <p className="text-sm text-red-700 mt-1">{error_message}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Pending state */}
        {status === 'pending' && (
          <div className="flex items-center gap-3 p-4 rounded-lg bg-gray-50 border border-gray-200">
            <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
              <div className="w-2 h-2 rounded-full bg-gray-400" />
            </div>
            <p className="text-sm text-gray-700">
              Document is queued for processing...
            </p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-lg">
        <div className="flex items-center gap-3 justify-end">
          {/* Cancel button (processing only) */}
          {isProcessing && onCancel && (
            <button
              onClick={() => onCancel(document_id)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel Processing
            </button>
          )}

          {/* Retry button (failed only) */}
          {status === 'failed' && onRetry && (
            <button
              onClick={() => onRetry(document_id)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              Retry Processing
            </button>
          )}

          {/* View analysis button (completed only) */}
          {status === 'completed' && onViewAnalysis && (
            <button
              onClick={() => onViewAnalysis(document_id)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              View Analysis
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
