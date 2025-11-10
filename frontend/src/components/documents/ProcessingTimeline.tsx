/**
 * ProcessingTimeline Component
 *
 * Visual timeline showing document processing stages
 * - Shows all 6 processing stages
 * - Visual indicators: completed (checkmark), in progress (spinner), pending (circle)
 * - Stage name, timestamp, and duration
 * - Animated transitions
 */

import React from 'react';
import { cn } from '../../lib/utils';
import { formatRelativeTime } from '../../lib/utils';
import type { DocumentStatus } from './DocumentStatusBadge';

export interface ProcessingStage {
  name: string;
  status: 'completed' | 'in_progress' | 'pending' | 'failed';
  timestamp?: Date | string;
  duration?: number; // in seconds
  error?: string;
}

interface ProcessingTimelineProps {
  currentStatus: DocumentStatus;
  stages?: ProcessingStage[];
  className?: string;
}

// Default stage configuration based on status
const defaultStages: Record<DocumentStatus, ProcessingStage[]> = {
  pending: [
    { name: 'Uploaded', status: 'completed' },
    { name: 'Extracting text', status: 'pending' },
    { name: 'Chunking text', status: 'pending' },
    { name: 'Generating embeddings', status: 'pending' },
    { name: 'Storing in database', status: 'pending' },
    { name: 'Completed', status: 'pending' },
  ],
  extracting: [
    { name: 'Uploaded', status: 'completed' },
    { name: 'Extracting text', status: 'in_progress' },
    { name: 'Chunking text', status: 'pending' },
    { name: 'Generating embeddings', status: 'pending' },
    { name: 'Storing in database', status: 'pending' },
    { name: 'Completed', status: 'pending' },
  ],
  chunking: [
    { name: 'Uploaded', status: 'completed' },
    { name: 'Extracting text', status: 'completed' },
    { name: 'Chunking text', status: 'in_progress' },
    { name: 'Generating embeddings', status: 'pending' },
    { name: 'Storing in database', status: 'pending' },
    { name: 'Completed', status: 'pending' },
  ],
  embedding: [
    { name: 'Uploaded', status: 'completed' },
    { name: 'Extracting text', status: 'completed' },
    { name: 'Chunking text', status: 'completed' },
    { name: 'Generating embeddings', status: 'in_progress' },
    { name: 'Storing in database', status: 'pending' },
    { name: 'Completed', status: 'pending' },
  ],
  storing: [
    { name: 'Uploaded', status: 'completed' },
    { name: 'Extracting text', status: 'completed' },
    { name: 'Chunking text', status: 'completed' },
    { name: 'Generating embeddings', status: 'completed' },
    { name: 'Storing in database', status: 'in_progress' },
    { name: 'Completed', status: 'pending' },
  ],
  completed: [
    { name: 'Uploaded', status: 'completed' },
    { name: 'Extracting text', status: 'completed' },
    { name: 'Chunking text', status: 'completed' },
    { name: 'Generating embeddings', status: 'completed' },
    { name: 'Storing in database', status: 'completed' },
    { name: 'Completed', status: 'completed' },
  ],
  failed: [
    { name: 'Uploaded', status: 'completed' },
    { name: 'Extracting text', status: 'failed' },
    { name: 'Chunking text', status: 'pending' },
    { name: 'Generating embeddings', status: 'pending' },
    { name: 'Storing in database', status: 'pending' },
    { name: 'Completed', status: 'pending' },
  ],
};

export function ProcessingTimeline({
  currentStatus,
  stages,
  className,
}: ProcessingTimelineProps) {
  const displayStages = stages || defaultStages[currentStatus];

  return (
    <div className={cn('space-y-4', className)}>
      <h3 className="text-sm font-medium text-gray-900">Processing Timeline</h3>

      <div className="relative">
        {/* Vertical line connecting stages */}
        <div className="absolute left-4 top-3 bottom-3 w-0.5 bg-gray-200" />

        {/* Stages */}
        <div className="space-y-6">
          {displayStages.map((stage, index) => (
            <TimelineStage
              key={index}
              stage={stage}
              isLast={index === displayStages.length - 1}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Individual timeline stage
 */
interface TimelineStageProps {
  stage: ProcessingStage;
  isLast: boolean;
}

function TimelineStage({ stage }: TimelineStageProps) {
  const { name, status, timestamp, duration, error } = stage;

  return (
    <div className="relative flex items-start gap-4">
      {/* Icon */}
      <div className="relative z-10 flex-shrink-0">
        {status === 'completed' && (
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 border-2 border-green-500">
            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}

        {status === 'in_progress' && (
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 border-2 border-blue-500">
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
          </div>
        )}

        {status === 'pending' && (
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 border-2 border-gray-300">
            <div className="w-3 h-3 rounded-full bg-gray-400" />
          </div>
        )}

        {status === 'failed' && (
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 border-2 border-red-500">
            <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-6">
        <div className="flex items-baseline justify-between gap-4">
          <p
            className={cn(
              'text-sm font-medium',
              status === 'completed' && 'text-green-900',
              status === 'in_progress' && 'text-blue-900',
              status === 'pending' && 'text-gray-500',
              status === 'failed' && 'text-red-900'
            )}
          >
            {name}
          </p>

          {timestamp && (
            <p className="text-xs text-gray-500 flex-shrink-0">
              {formatRelativeTime(timestamp)}
            </p>
          )}
        </div>

        {/* Duration */}
        {duration !== undefined && status === 'completed' && (
          <p className="text-xs text-gray-500 mt-1">
            Completed in {duration < 60 ? `${duration}s` : `${Math.floor(duration / 60)}m ${duration % 60}s`}
          </p>
        )}

        {/* Error message */}
        {error && status === 'failed' && (
          <div className="mt-2 p-2 rounded-md bg-red-50 border border-red-200">
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}

        {/* Progress indicator for in-progress stage */}
        {status === 'in_progress' && (
          <div className="mt-2">
            <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-blue-600 rounded-full animate-pulse" style={{ width: '60%' }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Compact timeline for smaller spaces
 */
export function CompactProcessingTimeline({
  currentStatus,
  className,
}: {
  currentStatus: DocumentStatus;
  className?: string;
}) {
  const stages = ['pending', 'extracting', 'chunking', 'embedding', 'storing', 'completed'];
  const currentIndex = stages.indexOf(currentStatus);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {stages.map((stage, index) => {
        const isCompleted = index < currentIndex;
        const isCurrent = index === currentIndex;
        const isPending = index > currentIndex;

        return (
          <React.Fragment key={stage}>
            <div
              className={cn(
                'w-2 h-2 rounded-full transition-colors',
                isCompleted && 'bg-green-500',
                isCurrent && 'bg-blue-500 animate-pulse',
                isPending && 'bg-gray-300'
              )}
            />
            {index < stages.length - 1 && (
              <div
                className={cn(
                  'h-0.5 w-8 transition-colors',
                  index < currentIndex ? 'bg-green-500' : 'bg-gray-300'
                )}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
