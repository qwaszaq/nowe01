/**
 * UploadModal Component
 *
 * Modal dialog for uploading documents to a case
 * - Case selector (if not already in case context)
 * - Drag and drop zone
 * - File list with remove buttons
 * - Upload button (disabled if no files)
 * - Close modal button
 * - Success message and redirect after upload
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { DocumentUpload } from './DocumentUpload';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId?: string;
  caseName?: string;
  onUploadComplete?: (documentId: string) => void;
  className?: string;
}

export function UploadModal({
  isOpen,
  onClose,
  caseId,
  caseName,
  onUploadComplete,
  className,
}: UploadModalProps) {
  const navigate = useNavigate();
  const [showSuccess, setShowSuccess] = useState(false);
  const [uploadedDocumentId, setUploadedDocumentId] = useState<string | null>(null);

  // Handle upload complete
  const handleUploadComplete = useCallback(
    (documentId: string) => {
      setUploadedDocumentId(documentId);
      setShowSuccess(true);

      // Call parent callback
      if (onUploadComplete) {
        onUploadComplete(documentId);
      }

      // Auto-close after 2 seconds and navigate
      setTimeout(() => {
        onClose();
        setShowSuccess(false);

        if (caseId) {
          navigate(`/cases/${caseId}/documents/${documentId}`);
        }
      }, 2000);
    },
    [onUploadComplete, onClose, navigate, caseId]
  );

  // Handle close
  const handleClose = useCallback(() => {
    if (!showSuccess) {
      onClose();
    }
  }, [showSuccess, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className={cn(
            'relative bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto',
            className
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-lg z-10">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Upload Documents</h2>
                {caseName && (
                  <p className="text-sm text-gray-600 mt-1">
                    Uploading to: <span className="font-medium">{caseName}</span>
                  </p>
                )}
              </div>
              <button
                onClick={handleClose}
                disabled={showSuccess}
                className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

          {/* Content */}
          <div className="px-6 py-6">
            {!showSuccess ? (
              <>
                {caseId ? (
                  <DocumentUpload
                    caseId={caseId}
                    onUploadComplete={handleUploadComplete}
                    autoRedirect={false}
                  />
                ) : (
                  <div className="text-center py-12">
                    <svg
                      className="w-12 h-12 text-gray-400 mx-auto mb-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                      />
                    </svg>
                    <p className="text-sm font-medium text-gray-900">No case selected</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Please select a case before uploading documents
                    </p>
                  </div>
                )}
              </>
            ) : (
              <SuccessMessage />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Success message component
 */
function SuccessMessage() {
  return (
    <div className="text-center py-12">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
        <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Successful!</h3>
      <p className="text-sm text-gray-600 mb-4">
        Your document has been uploaded and is being processed.
      </p>
      <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
        <svg
          className="w-4 h-4 animate-spin"
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
        <span>Redirecting to document status...</span>
      </div>
    </div>
  );
}

/**
 * Simplified upload button that opens the modal
 */
interface UploadButtonProps {
  caseId?: string;
  caseName?: string;
  onUploadComplete?: (documentId: string) => void;
  className?: string;
  variant?: 'primary' | 'secondary';
  children?: React.ReactNode;
}

export function UploadButton({
  caseId,
  caseName,
  onUploadComplete,
  className,
  variant = 'primary',
  children,
}: UploadButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const buttonClasses = cn(
    'inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors',
    variant === 'primary' &&
      'text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
    variant === 'secondary' &&
      'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
    className
  );

  return (
    <>
      <button onClick={() => setIsModalOpen(true)} className={buttonClasses}>
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        {children || 'Upload Document'}
      </button>

      <UploadModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        caseId={caseId}
        caseName={caseName}
        onUploadComplete={onUploadComplete}
      />
    </>
  );
}
