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
import { ActivityLog } from '../components/activity/ActivityLog';
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
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-slate-50 to-gray-100">
        <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 px-6 py-8">
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
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-slate-50 to-gray-100">
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
    { id: 'documents', name: 'Documents', icon: DocumentTextIcon, color: 'blue' },
    { id: 'analysis', name: 'Analysis Results', icon: ChartBarIcon, color: 'slate' },
    { id: 'activity', name: 'Activity', icon: ClockIcon, color: 'teal' },
  ];

  const getTabColorClasses = (color: string, isActive: boolean) => {
    const colors: Record<string, { active: string; inactive: string }> = {
      blue: {
        active: 'bg-gradient-to-r from-blue-50 to-blue-100 border-b-4 border-blue-600 text-blue-800',
        inactive: 'border-transparent text-gray-600 hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-blue-100/50 hover:text-blue-700'
      },
      slate: {
        active: 'bg-gradient-to-r from-slate-100 to-slate-200 border-b-4 border-slate-700 text-slate-800',
        inactive: 'border-transparent text-gray-600 hover:bg-gradient-to-r hover:from-slate-50/50 hover:to-slate-100/50 hover:text-slate-700'
      },
      teal: {
        active: 'bg-gradient-to-r from-teal-50 to-teal-100 border-b-4 border-teal-600 text-teal-800',
        inactive: 'border-transparent text-gray-600 hover:bg-gradient-to-r hover:from-teal-50/50 hover:to-teal-100/50 hover:text-teal-700'
      },
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-gray-50 to-gray-100 relative">
      {/* Subtle Grid Pattern Background */}
      <div className="absolute inset-0 opacity-[0.015] pointer-events-none" style={{
        backgroundImage: `
          linear-gradient(to right, #000 1px, transparent 1px),
          linear-gradient(to bottom, #000 1px, transparent 1px)
        `,
        backgroundSize: '40px 40px'
      }}></div>
      <div className="relative z-10">
      {/* Case Header */}
      <CaseHeader case={caseData} onDelete={handleDelete} />

      {/* Main Content */}
      <div className="px-4 sm:px-6 lg:px-8 py-8 max-w-7xl mx-auto">
        {/* Stats */}
        <div className="mb-8">
          <CaseStats caseId={caseData.id} />
        </div>

        {/* Tabs */}
        <div className="bg-white border border-gray-200/60 rounded-xl shadow-md overflow-hidden">
          {/* Tab Navigation */}
          <div className="bg-gradient-to-r from-gray-50 to-slate-100/30">
            <nav className="-mb-px flex gap-2 px-6 pt-4" aria-label="Tabs">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                const colorClasses = getTabColorClasses(tab.color, isActive);
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as TabType)}
                    className={`${
                      isActive ? colorClasses.active : colorClasses.inactive
                    } whitespace-nowrap py-3 px-5 font-semibold text-sm flex items-center rounded-t-xl transition-all duration-200 shadow-sm`}
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
              <ActivityLog caseId={caseId!} />
            )}
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}
