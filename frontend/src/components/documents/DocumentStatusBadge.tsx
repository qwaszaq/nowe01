/**
 * DocumentStatusBadge Component
 *
 * Color-coded status badge for documents with optional spinner animation
 */

import { cn } from '../../lib/utils';

export type DocumentStatus =
  | 'pending'
  | 'extracting'
  | 'chunking'
  | 'embedding'
  | 'storing'
  | 'completed'
  | 'failed';

interface DocumentStatusBadgeProps {
  status: DocumentStatus;
  className?: string;
  showIcon?: boolean;
}

const statusConfig = {
  pending: {
    label: 'Pending',
    className: 'bg-gray-100 text-gray-800 border-gray-300',
    icon: '○',
  },
  extracting: {
    label: 'Extracting',
    className: 'bg-blue-100 text-blue-800 border-blue-300',
    icon: '↻',
    animated: true,
  },
  chunking: {
    label: 'Chunking',
    className: 'bg-blue-100 text-blue-800 border-blue-300',
    icon: '↻',
    animated: true,
  },
  embedding: {
    label: 'Embedding',
    className: 'bg-blue-100 text-blue-800 border-blue-300',
    icon: '↻',
    animated: true,
  },
  storing: {
    label: 'Storing',
    className: 'bg-blue-100 text-blue-800 border-blue-300',
    icon: '↻',
    animated: true,
  },
  completed: {
    label: 'Completed',
    className: 'bg-green-100 text-green-800 border-green-300',
    icon: '✓',
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-100 text-red-800 border-red-300',
    icon: '✗',
  },
};

export function DocumentStatusBadge({
  status,
  className,
  showIcon = true,
}: DocumentStatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
        config.className,
        className
      )}
    >
      {showIcon && (
        <span
          className={cn(
            'inline-block',
            'animated' in config && config.animated && 'animate-spin'
          )}
        >
          {config.icon}
        </span>
      )}
      {config.label}
    </span>
  );
}

/**
 * Helper function to check if a status is processing
 */
export function isProcessingStatus(status: DocumentStatus): boolean {
  return ['extracting', 'chunking', 'embedding', 'storing'].includes(status);
}

/**
 * Helper function to check if a status is final
 */
export function isFinalStatus(status: DocumentStatus): boolean {
  return status === 'completed' || status === 'failed';
}

/**
 * Get progress percentage for a status
 */
export function getStatusProgress(status: DocumentStatus): number {
  const progressMap: Record<DocumentStatus, number> = {
    pending: 0,
    extracting: 20,
    chunking: 40,
    embedding: 60,
    storing: 80,
    completed: 100,
    failed: 0,
  };
  return progressMap[status];
}

/**
 * Get human-readable stage description
 */
export function getStageDescription(status: DocumentStatus): string {
  const descriptions: Record<DocumentStatus, string> = {
    pending: 'Waiting to start processing...',
    extracting: 'Extracting text from PDF...',
    chunking: 'Chunking text into segments...',
    embedding: 'Generating semantic embeddings...',
    storing: 'Storing in database...',
    completed: 'Processing complete',
    failed: 'Processing failed',
  };
  return descriptions[status];
}
