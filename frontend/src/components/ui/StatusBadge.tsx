/**
 * StatusBadge Component
 * Color-coded badge for displaying case and document status
 */

import { CaseStatus, DocumentStatus, AnalysisStatus } from '../../types';

interface StatusBadgeProps {
  status: CaseStatus | DocumentStatus | AnalysisStatus;
  className?: string;
}

const STATUS_STYLES: Record<string, string> = {
  // Case statuses
  [CaseStatus.OPEN]: 'bg-blue-100 text-blue-800 border-blue-200',
  [CaseStatus.IN_PROGRESS]: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  [CaseStatus.UNDER_REVIEW]: 'bg-purple-100 text-purple-800 border-purple-200',
  [CaseStatus.COMPLETED]: 'bg-green-100 text-green-800 border-green-200',
  [CaseStatus.ARCHIVED]: 'bg-gray-100 text-gray-800 border-gray-200',
  [CaseStatus.CLOSED]: 'bg-gray-100 text-gray-600 border-gray-200',

  // Document statuses
  [DocumentStatus.PENDING]: 'bg-gray-100 text-gray-600 border-gray-200',
  [DocumentStatus.VALIDATING]: 'bg-blue-100 text-blue-700 border-blue-200',
  [DocumentStatus.EXTRACTING]: 'bg-blue-100 text-blue-700 border-blue-200',
  [DocumentStatus.CHUNKING]: 'bg-blue-100 text-blue-700 border-blue-200',
  [DocumentStatus.EMBEDDING]: 'bg-blue-100 text-blue-700 border-blue-200',
  [DocumentStatus.STORING]: 'bg-blue-100 text-blue-700 border-blue-200',
  [DocumentStatus.COMPLETED]: 'bg-green-100 text-green-800 border-green-200',
  [DocumentStatus.FAILED]: 'bg-red-100 text-red-800 border-red-200',

  // Analysis statuses
  [AnalysisStatus.QUEUED]: 'bg-gray-100 text-gray-600 border-gray-200',
  [AnalysisStatus.SEARCHING]: 'bg-blue-100 text-blue-700 border-blue-200',
  [AnalysisStatus.CALCULATING]: 'bg-blue-100 text-blue-700 border-blue-200',
  [AnalysisStatus.CLASSIFYING]: 'bg-blue-100 text-blue-700 border-blue-200',
  [AnalysisStatus.COMPLETED]: 'bg-green-100 text-green-800 border-green-200',
  [AnalysisStatus.FAILED]: 'bg-red-100 text-red-800 border-red-200',
};

const STATUS_LABELS: Record<string, string> = {
  // Case statuses
  [CaseStatus.OPEN]: 'Open',
  [CaseStatus.IN_PROGRESS]: 'In Progress',
  [CaseStatus.UNDER_REVIEW]: 'Under Review',
  [CaseStatus.COMPLETED]: 'Completed',
  [CaseStatus.ARCHIVED]: 'Archived',
  [CaseStatus.CLOSED]: 'Closed',

  // Document statuses
  [DocumentStatus.PENDING]: 'Pending',
  [DocumentStatus.VALIDATING]: 'Validating',
  [DocumentStatus.EXTRACTING]: 'Extracting',
  [DocumentStatus.CHUNKING]: 'Chunking',
  [DocumentStatus.EMBEDDING]: 'Embedding',
  [DocumentStatus.STORING]: 'Storing',
  [DocumentStatus.COMPLETED]: 'Completed',
  [DocumentStatus.FAILED]: 'Failed',

  // Analysis statuses
  [AnalysisStatus.QUEUED]: 'Queued',
  [AnalysisStatus.SEARCHING]: 'Searching',
  [AnalysisStatus.CALCULATING]: 'Calculating',
  [AnalysisStatus.CLASSIFYING]: 'Classifying',
  [AnalysisStatus.COMPLETED]: 'Completed',
  [AnalysisStatus.FAILED]: 'Failed',
};

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const styles = STATUS_STYLES[status] || 'bg-gray-100 text-gray-800 border-gray-200';
  const label = STATUS_LABELS[status] || status;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles} ${className}`}
    >
      {label}
    </span>
  );
}
