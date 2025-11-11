/**
 * CaseHeader Component
 * Header section for case details page with actions
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ChevronRightIcon,
  PencilIcon,
  ArchiveBoxIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { StatusBadge } from '../ui/StatusBadge';
import { EditCaseForm } from './EditCaseForm';
import { DeleteCaseDialog } from './DeleteCaseDialog';
import { useUpdateCase } from '../../hooks/useCases';
import type { Case } from '../../types';
import { CaseStatus } from '../../types';

interface CaseHeaderProps {
  case: Case;
  onDelete?: () => void;
}

export function CaseHeader({ case: caseData, onDelete }: CaseHeaderProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const updateCase = useUpdateCase();

  const handleArchive = async () => {
    try {
      await updateCase.mutateAsync({
        caseId: caseData.id,
        request: { status: CaseStatus.ARCHIVED },
      });
    } catch (error) {
      console.error('Failed to archive case:', error);
    }
  };

  return (
    <>
      <div className="fixed top-16 lg:top-0 left-0 lg:left-64 right-0 z-30 bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8 py-4">
          {/* Breadcrumb */}
          <nav className="flex items-center text-sm text-gray-600 mb-4">
            <Link to="/" className="hover:text-blue-600 transition-colors font-medium">
              Dashboard
            </Link>
            <ChevronRightIcon className="h-4 w-4 mx-2 text-gray-400" />
            <Link to="/" className="hover:text-blue-600 transition-colors font-medium">
              Cases
            </Link>
            <ChevronRightIcon className="h-4 w-4 mx-2 text-gray-400" />
            <span className="font-semibold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">{caseData.name}</span>
          </nav>

          {!isEditing ? (
            <>
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">{caseData.name}</h1>
                    <StatusBadge status={caseData.status} />
                  </div>
                  {caseData.description && (
                    <p className="text-gray-600 max-w-3xl leading-relaxed">{caseData.description}</p>
                  )}
                  <div className="flex items-center gap-3 mt-3 text-sm">
                    <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full font-medium">
                      Created {format(new Date(caseData.created_at), 'MMM d, yyyy')}
                    </span>
                    <span className="text-gray-400">•</span>
                    <span className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full font-medium">
                      Updated {format(new Date(caseData.updated_at), 'MMM d, yyyy')}
                    </span>
                    {caseData.document_count !== undefined && (
                      <>
                        <span className="text-gray-400">•</span>
                        <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full font-medium">
                          {caseData.document_count} documents
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 ml-4">
                  <button
                    onClick={() => setIsEditing(true)}
                    className="inline-flex items-center px-4 py-2 border-2 border-gray-300 rounded-lg text-sm font-semibold text-gray-700 bg-white hover:bg-gradient-to-r hover:from-slate-50 hover:to-slate-100 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 transition-all duration-200 shadow-sm hover:shadow-md"
                  >
                    <PencilIcon className="h-4 w-4 mr-2" />
                    Edit
                  </button>

                  {caseData.status !== CaseStatus.ARCHIVED && (
                    <button
                      onClick={handleArchive}
                      disabled={updateCase.isPending}
                      className="inline-flex items-center px-4 py-2 border-2 border-gray-300 rounded-lg text-sm font-semibold text-gray-700 bg-white hover:bg-gradient-to-r hover:from-slate-50 hover:to-slate-100 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 disabled:opacity-50 transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      <ArchiveBoxIcon className="h-4 w-4 mr-2" />
                      {updateCase.isPending ? 'Archiving...' : 'Archive'}
                    </button>
                  )}

                  <button
                    onClick={() => setShowDeleteDialog(true)}
                    className="inline-flex items-center px-4 py-2 border-2 border-red-300 rounded-lg text-sm font-semibold text-red-700 bg-white hover:bg-red-50 hover:border-red-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-all duration-200 shadow-sm hover:shadow-md"
                  >
                    <TrashIcon className="h-4 w-4 mr-2" />
                    Delete
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="max-w-3xl">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Edit Case</h2>
              <EditCaseForm
                case={caseData}
                onSuccess={() => setIsEditing(false)}
                onCancel={() => setIsEditing(false)}
              />
            </div>
          )}
        </div>
      </div>

      {/* Delete Dialog */}
      <DeleteCaseDialog
        case={caseData}
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onSuccess={onDelete}
      />
    </>
  );
}
