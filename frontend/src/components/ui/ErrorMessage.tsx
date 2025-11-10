/**
 * ErrorMessage Component
 * Display error messages with retry option
 */

import { XCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface ErrorMessageProps {
  error: Error | { message: string; detail?: string };
  onRetry?: () => void;
  className?: string;
  variant?: 'inline' | 'page' | 'toast';
}

export function ErrorMessage({
  error,
  onRetry,
  className = '',
  variant = 'inline',
}: ErrorMessageProps) {
  const message = error?.message || 'An error occurred';
  const detail = 'detail' in error ? error.detail : undefined;

  if (variant === 'page') {
    return (
      <div className={`min-h-[400px] flex items-center justify-center ${className}`}>
        <div className="text-center max-w-md">
          <XCircleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Something went wrong</h3>
          <p className="text-gray-600 mb-2">{message}</p>
          {detail && <p className="text-sm text-gray-500 mb-4">{detail}</p>}
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  if (variant === 'toast') {
    return (
      <div
        className={`bg-red-50 border border-red-200 rounded-lg p-4 flex items-start ${className}`}
      >
        <XCircleIcon className="h-5 w-5 text-red-500 mr-3 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium text-red-800">{message}</p>
          {detail && <p className="text-sm text-red-700 mt-1">{detail}</p>}
        </div>
      </div>
    );
  }

  // inline variant
  return (
    <div
      className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}
      role="alert"
    >
      <div className="flex items-start">
        <XCircleIcon className="h-5 w-5 text-red-500 mr-3 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-red-800 mb-1">Error</h4>
          <p className="text-sm text-red-700">{message}</p>
          {detail && <p className="text-xs text-red-600 mt-2">{detail}</p>}
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center px-3 py-1.5 border border-red-300 rounded-md text-xs font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <ArrowPathIcon className="h-3 w-3 mr-1.5" />
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * EmptyState Component
 * Display when there's no data
 */
interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon,
  action,
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`text-center py-12 ${className}`}>
      {Icon && <Icon className="h-12 w-12 text-gray-400 mx-auto mb-4" />}
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      {description && <p className="text-gray-600 mb-6 max-w-md mx-auto">{description}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
