/**
 * UploadProgress Component
 *
 * Shows upload progress for multiple files with individual progress bars
 * - Upload percentage for each file
 * - Upload speed calculation
 * - Cancel button for each file
 * - Overall progress summary
 */

import { cn } from '../../lib/utils';
import { formatFileSize } from '../../lib/fileValidation';

export interface FileUploadProgress {
  file: File;
  progress: number; // 0-100
  uploadedBytes: number;
  totalBytes: number;
  speed?: number; // bytes per second
  status: 'uploading' | 'completed' | 'error' | 'cancelled';
  error?: string;
}

interface UploadProgressProps {
  uploads: FileUploadProgress[];
  onCancel?: (file: File) => void;
  className?: string;
}

export function UploadProgress({ uploads, onCancel, className }: UploadProgressProps) {
  const completedCount = uploads.filter((u) => u.status === 'completed').length;
  const totalCount = uploads.length;
  const overallProgress = totalCount > 0
    ? (completedCount / totalCount) * 100
    : 0;

  if (uploads.length === 0) return null;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Overall progress header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">
          Uploading files
        </h3>
        <span className="text-sm text-gray-600">
          {completedCount} of {totalCount} completed
        </span>
      </div>

      {/* Overall progress bar */}
      <div className="relative">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all duration-300 ease-out"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {overallProgress.toFixed(0)}% overall progress
        </p>
      </div>

      {/* Individual file progress */}
      <div className="space-y-3">
        {uploads.map((upload, index) => (
          <FileUploadItem
            key={`${upload.file.name}-${index}`}
            upload={upload}
            onCancel={onCancel}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Individual file upload progress item
 */
interface FileUploadItemProps {
  upload: FileUploadProgress;
  onCancel?: (file: File) => void;
}

function FileUploadItem({ upload, onCancel }: FileUploadItemProps) {
  const { file, progress, uploadedBytes, totalBytes, speed, status, error } = upload;

  const speedMBps = speed ? speed / (1024 * 1024) : 0;
  const remainingBytes = totalBytes - uploadedBytes;
  const remainingTime = speed && speed > 0 ? remainingBytes / speed : 0;

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${Math.ceil(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.ceil(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  return (
    <div
      className={cn(
        'p-4 rounded-lg border transition-colors',
        status === 'uploading' && 'border-blue-200 bg-blue-50/50',
        status === 'completed' && 'border-green-200 bg-green-50/50',
        status === 'error' && 'border-red-200 bg-red-50/50',
        status === 'cancelled' && 'border-gray-200 bg-gray-50'
      )}
    >
      <div className="flex items-start justify-between gap-3">
        {/* File info */}
        <div className="flex items-start gap-3 flex-1 min-w-0">
          {/* Icon/Status */}
          <div className="flex-shrink-0 mt-1">
            {status === 'uploading' && (
              <svg
                className="w-5 h-5 text-blue-600 animate-spin"
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
            )}
            {status === 'completed' && (
              <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            {status === 'error' && (
              <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            {status === 'cancelled' && (
              <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </div>

          {/* File details */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>

            {/* Progress bar */}
            {status === 'uploading' && (
              <div className="mt-2">
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-300 ease-out"
                    style={{ width: `${Number(progress) || 0}%` }}
                  />
                </div>
              </div>
            )}

            {/* Status text */}
            <div className="mt-2 flex items-center gap-3 text-xs text-gray-600">
              {status === 'uploading' && (
                <>
                  <span>
                    {formatFileSize(uploadedBytes)} / {formatFileSize(totalBytes)}
                  </span>
                  <span>•</span>
                  <span>{(Number(progress) || 0).toFixed(0)}%</span>
                  {speed && speed > 0 && (
                    <>
                      <span>•</span>
                      <span>{speedMBps.toFixed(1)} MB/s</span>
                      {remainingTime > 0 && (
                        <>
                          <span>•</span>
                          <span>{formatTime(remainingTime)} remaining</span>
                        </>
                      )}
                    </>
                  )}
                </>
              )}
              {status === 'completed' && (
                <span className="text-green-600 font-medium">Upload complete</span>
              )}
              {status === 'error' && (
                <span className="text-red-600 font-medium">{error || 'Upload failed'}</span>
              )}
              {status === 'cancelled' && (
                <span className="text-gray-500 font-medium">Upload cancelled</span>
              )}
            </div>
          </div>
        </div>

        {/* Cancel button */}
        {status === 'uploading' && onCancel && (
          <button
            onClick={() => onCancel(file)}
            className="flex-shrink-0 p-1 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
            title="Cancel upload"
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
        )}
      </div>
    </div>
  );
}
