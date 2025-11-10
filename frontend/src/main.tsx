/**
 * Application Entry Point
 * Initializes React, React Query, Router, and global providers
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ErrorBoundary } from 'react-error-boundary';

import App from './App';
import { queryClient } from './lib/queryClient';
import './index.css';

/**
 * Error Fallback Component
 * Displayed when an unhandled error occurs in the application
 */
function ErrorFallback({ error, resetErrorBoundary }: any) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
          <svg
            className="w-6 h-6 text-red-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h2 className="mt-4 text-xl font-bold text-center text-gray-900">
          Something went wrong
        </h2>
        <p className="mt-2 text-sm text-center text-gray-600">
          {error?.message || 'An unexpected error occurred'}
        </p>
        {import.meta.env.DEV && (
          <pre className="mt-4 p-4 bg-gray-100 rounded text-xs overflow-auto max-h-48">
            {error?.stack}
          </pre>
        )}
        <button
          onClick={resetErrorBoundary}
          className="mt-6 w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

/**
 * Error handler callback
 */
function onError(error: Error, info: { componentStack: string }) {
  console.error('[Error Boundary]', error);
  console.error('[Component Stack]', info.componentStack);

  // You can send errors to an error reporting service here
  // Example: Sentry.captureException(error);
}

/**
 * Mount the application
 */
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary FallbackComponent={ErrorFallback} onError={onError}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>

        {/* React Query DevTools - only in development */}
        {import.meta.env.DEV && import.meta.env.VITE_ENABLE_QUERY_DEVTOOLS !== 'false' && (
          <ReactQueryDevtools initialIsOpen={false} position="bottom-right" />
        )}
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
