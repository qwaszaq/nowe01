/**
 * Settings Page
 * Administrative settings and system controls
 */

import { useState } from 'react';
import { ArrowPathIcon, ServerIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

export default function Settings() {
  const [isReinitializing, setIsReinitializing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleReinitialize = async () => {
    setIsReinitializing(true);
    setMessage(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/system/reinitialize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.ok) {
        const data = await response.json();
        setMessage({
          type: 'success',
          text: data.message || 'Services reinitialized successfully!'
        });
      } else {
        const error = await response.json();
        setMessage({
          type: 'error',
          text: error.detail || 'Failed to reinitialize services'
        });
      }
    } catch (error) {
      console.error('Reinitialize error:', error);
      setMessage({
        type: 'error',
        text: 'Error connecting to server. Please check if the backend is running.'
      });
    } finally {
      setIsReinitializing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-gray-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8 py-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tight leading-tight bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">
              Settings
            </h1>
            <p className="mt-2 text-sm text-gray-600 leading-relaxed">
              System configuration and administrative controls
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
        {/* System Administration Section */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-blue-50 border-b border-gray-200">
            <h2 className="text-lg font-bold text-slate-800 flex items-center">
              <ServerIcon className="w-6 h-6 mr-2 text-blue-600" />
              System Administration
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Advanced system controls and maintenance operations
            </p>
          </div>

          <div className="p-6 space-y-6">
            {/* Reinitialize Services */}
            <div className="border border-gray-200 rounded-lg p-5 bg-gradient-to-br from-white to-slate-50">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-base font-bold text-slate-900 flex items-center">
                    <ArrowPathIcon className="w-5 h-5 mr-2 text-orange-600" />
                    Reinitialize All Services
                  </h3>
                  <p className="text-sm text-gray-600 mt-2">
                    Restarts all backend services including E5 Embeddings, Semantic Search, LM Studio Client,
                    Micro Agents, and Analysis Flow. Use this when services become unresponsive or after
                    configuration changes.
                  </p>

                  {/* Status Message */}
                  {message && (
                    <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 ${
                      message.type === 'success'
                        ? 'bg-green-50 border border-green-200 text-green-800'
                        : 'bg-red-50 border border-red-200 text-red-800'
                    }`}>
                      {message.type === 'success' ? (
                        <CheckCircleIcon className="w-5 h-5 flex-shrink-0" />
                      ) : (
                        <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
                      )}
                      <span className="text-sm font-medium">{message.text}</span>
                    </div>
                  )}
                </div>

                <button
                  onClick={handleReinitialize}
                  disabled={isReinitializing}
                  className={`ml-4 flex items-center gap-2 px-5 py-2.5 rounded-lg font-semibold text-sm transition-all duration-200 shadow-md ${
                    isReinitializing
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white hover:shadow-lg'
                  }`}
                >
                  <ArrowPathIcon className={`w-5 h-5 ${isReinitializing ? 'animate-spin' : ''}`} />
                  {isReinitializing ? 'Reinitializing...' : 'Reinitialize'}
                </button>
              </div>
            </div>

            {/* Placeholder for future settings */}
            <div className="border border-dashed border-gray-300 rounded-lg p-5 bg-gray-50/50">
              <p className="text-sm text-gray-500 text-center">
                Additional system settings will appear here
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
