/**
 * DocumentDetails Page
 *
 * Route: /cases/:caseId/documents/:documentId
 *
 * Displays detailed information about a document with real-time status updates
 * - Document header (filename, upload date, file size)
 * - Status card with real-time updates (polling every 2 seconds while processing)
 * - Processing timeline showing all stages
 * - Action buttons (View Analysis, Retry, Delete)
 * - Document metadata (page count, chunk count)
 * - Activity timeline (uploaded, extracting, chunking, etc.)
 */

import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { formatFileSize } from '../lib/fileValidation';
import { formatDate, formatRelativeTime } from '../lib/utils';
import { DocumentStatusCard, type DocumentStatusData } from '../components/documents/DocumentStatusCard';
import { ProcessingTimeline } from '../components/documents/ProcessingTimeline';
import {
  DocumentStatusBadge,
  isProcessingStatus,
  type DocumentStatus,
} from '../components/documents/DocumentStatusBadge';
import { useDocument } from '../hooks/useDocuments';

export default function DocumentDetails() {
  const { caseId, documentId } = useParams<{ caseId: string; documentId: string }>();
  const navigate = useNavigate();

  // Fetch document data from API
  const { data: documentData, isLoading, error } = useDocument(documentId || '');

  // Map API document data to DocumentStatusData format
  const document: DocumentStatusData | null = documentData ? {
    document_id: documentData.document_id,
    filename: documentData.original_filename,
    file_size: documentData.file_size,
    status: documentData.status as DocumentStatus,
    progress_percent: documentData.status === 'completed' ? 100 : (documentData.status === 'failed' ? 0 : undefined),
    current_stage: documentData.status === 'completed' ? 'Przetwarzanie zakończone' :
                   documentData.status === 'failed' ? 'Błąd przetwarzania' :
                   documentData.status,
    chunks_processed: documentData.chunk_count || 0,
    total_chunks: documentData.chunk_count || 0,
    uploaded_at: documentData.uploaded_at,
    completed_at: documentData.processing_completed_at,
    error_message: documentData.error_message,
  } : null;

  // Handle actions
  const handleCancel = (docId: string) => {
    console.log('Cancel processing:', docId);
    // In real implementation: call cancel API
  };

  const handleRetry = (docId: string) => {
    console.log('Retry processing:', docId);
    // In real implementation: call retry API
  };

  const handleViewAnalysis = (docId: string) => {
    navigate(`/cases/${caseId}/documents/${docId}/analysis`);
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      console.log('Delete document:', documentId);
      // In real implementation: call delete API
      navigate(`/cases/${caseId}`);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white via-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center p-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/60">
          <svg
            className="w-16 h-16 text-slate-700 animate-spin mx-auto mb-4"
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
          <p className="text-base font-semibold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">
            Ładowanie szczegółów dokumentu...
          </p>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white via-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center p-12 bg-white rounded-2xl shadow-xl border border-gray-200/60 max-w-md">
          <svg
            className="w-16 h-16 text-gray-400 mx-auto mb-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-lg font-bold text-gray-900">Dokument nie został znaleziony</p>
          <p className="text-sm text-gray-600 mt-2">
            Dokument którego szukasz nie istnieje lub został usunięty.
          </p>
          <Link
            to={`/cases/${caseId}`}
            className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-slate-700 to-slate-900 hover:from-slate-800 hover:to-black rounded-lg shadow-md hover:shadow-lg transform transition-all duration-200 hover:scale-105"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Powrót do sprawy
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-gray-50 to-gray-100">
      {/* Header - Fixed */}
      <div className="fixed top-16 lg:top-0 left-0 lg:left-64 right-0 z-30 bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8 py-6">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-2 text-sm text-gray-600 mb-4">
            <Link to="/cases" className="hover:text-blue-600 transition-colors font-medium">
              Sprawy
            </Link>
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            <Link to={`/cases/${caseId}`} className="hover:text-blue-600 transition-colors font-medium">
              Szczegóły sprawy
            </Link>
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            <span className="font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Szczegóły dokumentu
            </span>
          </nav>

          {/* Document header */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4 flex-1 min-w-0">
              {/* PDF icon */}
              <div className="flex-shrink-0 p-3 bg-gradient-to-br from-red-500 to-pink-600 rounded-xl shadow-lg">
                <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>

              {/* Document info */}
              <div className="flex-1 min-w-0">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent truncate" title={document.filename}>
                  {document.filename}
                </h1>
                <div className="mt-3 flex items-center gap-3 text-sm">
                  <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full font-medium">
                    {formatFileSize(document.file_size)}
                  </span>
                  <span className="text-gray-400">•</span>
                  <span className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full font-medium">
                    Przesłano {document.uploaded_at ? formatRelativeTime(document.uploaded_at) : 'niedawno'}
                  </span>
                  <span className="text-gray-400">•</span>
                  <DocumentStatusBadge status={document.status} />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={handleDelete}
                className="px-5 py-2.5 text-sm font-semibold text-red-600 bg-white border-2 border-red-300 rounded-lg hover:bg-red-50 hover:border-red-400 transition-all duration-200 shadow-sm hover:shadow-md"
              >
                Usuń
              </button>
              {document.status === 'completed' && (
                <button
                  onClick={() => handleViewAnalysis(document.document_id)}
                  className="px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-slate-700 to-slate-900 hover:from-slate-800 hover:to-black rounded-lg shadow-md hover:shadow-lg transform transition-all duration-200 hover:scale-105"
                >
                  Zobacz analizę →
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Content - Add top padding to account for fixed header */}
      <div className="pt-56 lg:pt-40 px-4 sm:px-6 lg:px-8 pb-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Status card */}
            <DocumentStatusCard
              document={document}
              onCancel={handleCancel}
              onViewAnalysis={handleViewAnalysis}
              onRetry={handleRetry}
            />

            {/* Document metadata (if completed) */}
            {document.status === 'completed' && (
              <div className="bg-white rounded-xl border border-gray-200/60 shadow-md p-6">
                <h2 className="text-xl font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent mb-6">
                  Metadane dokumentu
                </h2>
                <dl className="grid grid-cols-2 gap-6">
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100/50 p-4 rounded-lg">
                    <dt className="text-sm font-semibold text-blue-600 mb-1">Liczba stron</dt>
                    <dd className="text-2xl font-bold text-gray-900">
                      {documentData?.page_count || 'N/A'}
                    </dd>
                  </div>
                  <div className="bg-gradient-to-br from-teal-50 to-teal-100/50 p-4 rounded-lg">
                    <dt className="text-sm font-semibold text-teal-600 mb-1">Fragmenty semantyczne</dt>
                    <dd className="text-2xl font-bold text-gray-900">
                      {document.total_chunks || 0}
                    </dd>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-green-100/50 p-4 rounded-lg">
                    <dt className="text-sm font-semibold text-green-600 mb-1">Data przesłania</dt>
                    <dd className="text-sm font-bold text-gray-900">
                      {document.uploaded_at ? formatDate(document.uploaded_at) : 'N/A'}
                    </dd>
                  </div>
                  {document.completed_at && (
                    <>
                      <div className="bg-gradient-to-br from-amber-50 to-amber-100/50 p-4 rounded-lg">
                        <dt className="text-sm font-semibold text-amber-600 mb-1">Data zakończenia</dt>
                        <dd className="text-sm font-bold text-gray-900">
                          {document.completed_at ? formatDate(document.completed_at) : 'N/A'}
                        </dd>
                      </div>
                      <div className="bg-gradient-to-br from-pink-50 to-pink-100/50 p-4 rounded-lg col-span-2">
                        <dt className="text-sm font-semibold text-pink-600 mb-1">Czas przetwarzania</dt>
                        <dd className="text-2xl font-bold text-gray-900">
                          {document.completed_at && document.uploaded_at ? Math.floor(
                            (new Date(document.completed_at).getTime() -
                              new Date(document.uploaded_at).getTime()) /
                              1000 /
                              60
                          ) : 0}{' '}
                          minut
                        </dd>
                      </div>
                    </>
                  )}
                </dl>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            {/* Processing timeline */}
            <div className="bg-white rounded-xl border border-gray-200/60 shadow-md p-6">
              <ProcessingTimeline currentStatus={document.status} />
            </div>

            {/* Quick actions */}
            <div className="bg-white rounded-xl border border-gray-200/60 shadow-md p-6">
              <h3 className="text-lg font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent mb-4">
                Szybkie akcje
              </h3>
              <div className="space-y-3">
                <button className="w-full text-left px-4 py-3 text-sm font-semibold text-gray-700 bg-gradient-to-r from-gray-50 to-blue-50/30 hover:from-blue-50 hover:to-purple-50 rounded-lg transition-all duration-200 flex items-center gap-3 border border-gray-200/60 hover:border-blue-300 shadow-sm hover:shadow-md">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  Pobierz PDF
                </button>
                <button className="w-full text-left px-4 py-3 text-sm font-semibold text-gray-700 bg-gradient-to-r from-gray-50 to-purple-50/30 hover:from-blue-50 hover:to-purple-50 rounded-lg transition-all duration-200 flex items-center gap-3 border border-gray-200/60 hover:border-purple-300 shadow-sm hover:shadow-md">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                  Zobacz PDF
                </button>
                {document.status === 'completed' && (
                  <button className="w-full text-left px-4 py-3 text-sm font-semibold text-gray-700 bg-gradient-to-r from-gray-50 to-green-50/30 hover:from-blue-50 hover:to-purple-50 rounded-lg transition-all duration-200 flex items-center gap-3 border border-gray-200/60 hover:border-green-300 shadow-sm hover:shadow-md">
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                    Uruchom nową analizę
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
