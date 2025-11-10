/**
 * DropZone Component
 *
 * Beautiful drag-and-drop file upload zone with validation
 * - Accepts PDF files only
 * - Maximum file size: 500MB
 * - Visual feedback for drag states
 * - File preview after selection
 */

import { useDropzone } from 'react-dropzone';
import { cn } from '../../lib/utils';
import { validateFile, formatFileSize } from '../../lib/fileValidation';

interface DropZoneProps {
  onFilesSelected: (files: File[]) => void;
  multiple?: boolean;
  disabled?: boolean;
  maxFiles?: number;
  className?: string;
}

export function DropZone({
  onFilesSelected,
  multiple = true,
  disabled = false,
  maxFiles,
  className,
}: DropZoneProps) {
  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject,
    fileRejections,
  } = useDropzone({
    onDrop: (acceptedFiles) => {
      // Validate files before passing them up
      const validFiles = acceptedFiles.filter((file) => {
        const result = validateFile(file);
        return result.valid;
      });

      if (validFiles.length > 0) {
        onFilesSelected(validFiles);
      }
    },
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxSize: 500 * 1024 * 1024, // 500MB
    multiple,
    maxFiles,
    disabled,
  });

  return (
    <div className={cn('w-full', className)}>
      <div
        {...getRootProps()}
        className={cn(
          'relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-200',
          'hover:border-gray-400 hover:bg-gray-50/50',
          isDragActive && !isDragReject && 'border-blue-500 bg-blue-50 border-solid',
          isDragReject && 'border-red-500 bg-red-50 border-solid',
          disabled && 'opacity-50 cursor-not-allowed hover:border-gray-300 hover:bg-transparent',
          !isDragActive && !isDragReject && 'border-gray-300'
        )}
      >
        <input {...getInputProps()} />

        {/* Icon */}
        <div className="flex justify-center mb-4">
          <svg
            className={cn(
              'w-16 h-16 transition-colors',
              isDragActive && !isDragReject && 'text-blue-500',
              isDragReject && 'text-red-500',
              !isDragActive && !isDragReject && 'text-gray-400'
            )}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
        </div>

        {/* Text */}
        <div className="space-y-2">
          {isDragActive && !isDragReject ? (
            <p className="text-lg font-medium text-blue-600">
              Drop your PDF files here...
            </p>
          ) : isDragReject ? (
            <p className="text-lg font-medium text-red-600">
              Only PDF files under 500MB are accepted
            </p>
          ) : (
            <>
              <p className="text-lg font-medium text-gray-700">
                Drag PDF files here or click to browse
              </p>
              <p className="text-sm text-gray-500">
                {multiple
                  ? `Upload one or more PDF files (max 500MB each)`
                  : 'Upload a single PDF file (max 500MB)'}
              </p>
            </>
          )}
        </div>

        {/* File type badge */}
        <div className="mt-4 flex justify-center">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-300">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                clipRule="evenodd"
              />
            </svg>
            PDF Only
          </span>
        </div>
      </div>

      {/* Error messages */}
      {fileRejections.length > 0 && (
        <div className="mt-4 space-y-2">
          {fileRejections.map(({ file, errors }) => (
            <div
              key={file.name}
              className="flex items-start gap-2 p-3 rounded-md bg-red-50 border border-red-200"
            >
              <svg
                className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
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
                <p className="text-sm font-medium text-red-800">{file.name}</p>
                {errors.map((error) => (
                  <p key={error.code} className="text-xs text-red-700 mt-1">
                    {error.message}
                  </p>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * FilePreview Component
 * Shows selected files with remove option
 */
interface FilePreviewProps {
  files: File[];
  onRemove: (file: File) => void;
  className?: string;
}

export function FilePreview({ files, onRemove, className }: FilePreviewProps) {
  if (files.length === 0) return null;

  return (
    <div className={cn('space-y-2', className)}>
      <h4 className="text-sm font-medium text-gray-700">
        Selected files ({files.length})
      </h4>
      <div className="space-y-2">
        {files.map((file, index) => (
          <div
            key={`${file.name}-${index}`}
            className="flex items-center justify-between gap-3 p-3 rounded-md bg-gray-50 border border-gray-200"
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {/* PDF Icon */}
              <svg
                className="w-8 h-8 text-red-500 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                  clipRule="evenodd"
                />
              </svg>

              {/* File info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
              </div>
            </div>

            {/* Remove button */}
            <button
              onClick={() => onRemove(file)}
              className="flex-shrink-0 p-1 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
              title="Remove file"
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
        ))}
      </div>
    </div>
  );
}
