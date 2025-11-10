/**
 * Case Details Page
 * Detailed view of a specific case with tabs for documents, analysis, and activity
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DocumentTextIcon, ChartBarIcon, ClockIcon, ArrowUpTrayIcon } from '@heroicons/react/24/outline';
import { useCase } from '../hooks/useCases';
import { useDocuments } from '../hooks/useDocuments';
import { CaseHeader } from '../components/cases/CaseHeader';
import { CaseStats } from '../components/cases/CaseStats';
import { DocumentUpload } from '../components/documents/DocumentUpload';
import { DocumentList } from '../components/documents/DocumentList';
import { SemanticSearch } from '../components/analysis/SemanticSearch';
import { LoadingSkeleton, Spinner } from '../components/ui/LoadingSkeleton';
import { ErrorMessage, EmptyState } from '../components/ui/ErrorMessage';

type TabType = 'documents' | 'analysis' | 'activity';

export default function CaseDetails() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('documents');

  const { data: caseData, isLoading, error } = useCase(caseId!);
  const { data: documentsData, refetch: refetchDocuments } = useDocuments(caseId!);

  const handleDelete = () => {
    navigate('/');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200 px-6 py-8">
          <LoadingSkeleton variant="text" count={3} />
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <LoadingSkeleton variant="stats" count={5} className="mb-8" />
          <LoadingSkeleton variant="card" count={3} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <ErrorMessage error={error} variant="page" />
        </div>
      </div>
    );
  }

  if (!caseData) {
    return null;
  }

  const tabs = [
    { id: 'documents', name: 'Documents', icon: DocumentTextIcon },
    { id: 'analysis', name: 'Analysis Results', icon: ChartBarIcon },
    { id: 'activity', name: 'Activity', icon: ClockIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Case Header */}
      <CaseHeader case={caseData} onDelete={handleDelete} />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="mb-8">
          <CaseStats caseId={caseData.id} />
        </div>

        {/* Tabs */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as TabType)}
                    className={`${
                      isActive
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
                  >
                    <Icon className="h-5 w-5 mr-2" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'documents' && (
              <div className="space-y-6">
                {/* Document Upload */}
                <DocumentUpload
                  caseId={caseId!}
                  onUploadComplete={() => refetchDocuments()}
                  autoRedirect={false}
                />

                {/* Document List */}
                {documentsData && documentsData.documents && documentsData.documents.length > 0 ? (
                  <DocumentList
                    documents={documentsData.documents}
                    onRefresh={refetchDocuments}
                  />
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <DocumentTextIcon className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                    <p>No documents uploaded yet. Upload your first PDF document above.</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'analysis' && (
              <div>
                <SemanticSearch caseId={caseId!} />
              </div>
            )}

            {activeTab === 'activity' && (
              <EmptyState
                title="Activity Log Coming Soon"
                description="Track all activities, changes, and events related to this case."
                icon={ClockIcon}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
