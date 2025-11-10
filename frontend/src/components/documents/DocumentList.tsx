/**
 * DocumentList Component
 *
 * Displays all documents for a case with filtering and sorting
 * - Table view with columns: filename, status, progress, date, actions
 * - Filter by status
 * - Sort by date
 * - Auto-refresh every 5 seconds if any documents are processing
 * - Integration with useDocuments() hook
 */

import { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { formatFileSize } from '../../lib/fileValidation';
import { formatRelativeTime, formatDate } from '../../lib/utils';
import {
  DocumentStatusBadge,
  isProcessingStatus,
  type DocumentStatus,
} from './DocumentStatusBadge';
import { CompactProcessingTimeline } from './ProcessingTimeline';

export interface Document {
  document_id: string;
  case_id: string;
  filename: string;
  file_size: number;
  status: DocumentStatus;
  progress_percent?: number;
  uploaded_at: Date | string;
  completed_at?: Date | string;
  error_message?: string;
}

interface DocumentListProps {
  caseId: string;
  documents: Document[];
  isLoading?: boolean;
  onRefresh?: () => void;
  onDelete?: (documentId: string) => void;
  className?: string;
}

type SortField = 'filename' | 'uploaded_at' | 'status';
type SortDirection = 'asc' | 'desc';

export function DocumentList({
  caseId,
  documents,
  isLoading = false,
  onRefresh,
  onDelete,
  className,
}: DocumentListProps) {
  const [filterStatus, setFilterStatus] = useState<DocumentStatus | 'all'>('all');
  const [sortField, setSortField] = useState<SortField>('uploaded_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Check if any documents are processing for auto-refresh
  const hasProcessingDocuments = useMemo(
    () => documents.some((doc) => isProcessingStatus(doc.status)),
    [documents]
  );

  // Auto-refresh every 5 seconds if processing
  useEffect(() => {
    if (!hasProcessingDocuments || !onRefresh) return;

    const interval = setInterval(() => {
      onRefresh();
    }, 5000);

    return () => clearInterval(interval);
  }, [hasProcessingDocuments, onRefresh]);

  // Filter documents
  const filteredDocuments = useMemo(() => {
    if (filterStatus === 'all') return documents;
    return documents.filter((doc) => doc.status === filterStatus);
  }, [documents, filterStatus]);

  // Sort documents
  const sortedDocuments = useMemo(() => {
    const sorted = [...filteredDocuments];

    sorted.sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      // Handle date sorting
      if (sortField === 'uploaded_at') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }

      // Handle string sorting
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [filteredDocuments, sortField, sortDirection]);

  // Toggle sort
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Status filter options
  const statusOptions: Array<{ value: DocumentStatus | 'all'; label: string }> = [
    { value: 'all', label: 'All Documents' },
    { value: 'pending', label: 'Pending' },
    { value: 'extracting', label: 'Extracting' },
    { value: 'chunking', label: 'Chunking' },
    { value: 'embedding', label: 'Embedding' },
    { value: 'storing', label: 'Storing' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
  ];

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with filters */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-gray-900">Documents</h2>
          <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
            {documents.length}
          </span>
          {hasProcessingDocuments && (
            <span className="flex items-center gap-1.5 text-xs text-blue-600">
              <svg
                className="w-3 h-3 animate-spin"
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
              Auto-refreshing
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Status filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as DocumentStatus | 'all')}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          {/* Refresh button */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 transition-colors"
              title="Refresh"
            >
              <svg
                className={cn('w-5 h-5', isLoading && 'animate-spin')}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {sortedDocuments.length === 0 ? (
          <div className="p-12 text-center">
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
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
            <p className="text-sm font-medium text-gray-900">No documents found</p>
            <p className="text-sm text-gray-500 mt-1">
              {filterStatus !== 'all'
                ? 'Try changing the filter'
                : 'Upload a document to get started'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('filename')}
                  >
                    <div className="flex items-center gap-2">
                      Filename
                      {sortField === 'filename' && (
                        <svg
                          className={cn(
                            'w-4 h-4 transition-transform',
                            sortDirection === 'desc' && 'rotate-180'
                          )}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('status')}
                  >
                    <div className="flex items-center gap-2">
                      Status
                      {sortField === 'status' && (
                        <svg
                          className={cn(
                            'w-4 h-4 transition-transform',
                            sortDirection === 'desc' && 'rotate-180'
                          )}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Progress
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('uploaded_at')}
                  >
                    <div className="flex items-center gap-2">
                      Uploaded
                      {sortField === 'uploaded_at' && (
                        <svg
                          className={cn(
                            'w-4 h-4 transition-transform',
                            sortDirection === 'desc' && 'rotate-180'
                          )}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedDocuments.map((document) => (
                  <DocumentRow
                    key={document.document_id}
                    document={document}
                    caseId={caseId}
                    onDelete={onDelete}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Individual document row
 */
interface DocumentRowProps {
  document: Document;
  caseId: string;
  onDelete?: (documentId: string) => void;
}

function DocumentRow({ document, caseId, onDelete }: DocumentRowProps) {
  const {
    document_id,
    filename,
    file_size,
    status,
    progress_percent,
    uploaded_at,
    error_message,
  } = document;

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      {/* Filename */}
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center gap-3">
          <svg className="w-8 h-8 text-red-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
              clipRule="evenodd"
            />
          </svg>
          <div className="min-w-0">
            <Link
              to={`/cases/${caseId}/documents/${document_id}`}
              className="text-sm font-medium text-gray-900 hover:text-blue-600 truncate block"
              title={filename}
            >
              {filename}
            </Link>
            <p className="text-xs text-gray-500">{formatFileSize(file_size)}</p>
          </div>
        </div>
      </td>

      {/* Status */}
      <td className="px-6 py-4 whitespace-nowrap">
        <DocumentStatusBadge status={status} />
      </td>

      {/* Progress */}
      <td className="px-6 py-4">
        {isProcessingStatus(status) ? (
          <div className="space-y-1 min-w-[200px]">
            <CompactProcessingTimeline currentStatus={status} />
            {progress_percent !== undefined && (
              <p className="text-xs text-gray-500">{progress_percent}%</p>
            )}
          </div>
        ) : status === 'completed' ? (
          <span className="text-sm text-green-600 font-medium">Complete</span>
        ) : status === 'failed' ? (
          <span className="text-sm text-red-600 font-medium" title={error_message}>
            Failed
          </span>
        ) : (
          <span className="text-sm text-gray-500">-</span>
        )}
      </td>

      {/* Uploaded */}
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900">{formatRelativeTime(uploaded_at)}</div>
        <div className="text-xs text-gray-500">{formatDate(uploaded_at)}</div>
      </td>

      {/* Actions */}
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="flex items-center justify-end gap-2">
          <Link
            to={`/cases/${caseId}/documents/${document_id}`}
            className="text-blue-600 hover:text-blue-900"
            title="View details"
          >
            View
          </Link>
          {onDelete && (
            <button
              onClick={() => onDelete(document_id)}
              className="text-red-600 hover:text-red-900"
              title="Delete document"
            >
              Delete
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
