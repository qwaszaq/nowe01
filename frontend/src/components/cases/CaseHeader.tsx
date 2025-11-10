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
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          {/* Breadcrumb */}
          <nav className="flex items-center text-sm text-gray-500 mb-4">
            <Link to="/" className="hover:text-gray-700">
              Dashboard
            </Link>
            <ChevronRightIcon className="h-4 w-4 mx-2" />
            <Link to="/" className="hover:text-gray-700">
              Cases
            </Link>
            <ChevronRightIcon className="h-4 w-4 mx-2" />
            <span className="text-gray-900 font-medium">{caseData.name}</span>
          </nav>

          {!isEditing ? (
            <>
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h1 className="text-2xl font-bold text-gray-900">{caseData.name}</h1>
                    <StatusBadge status={caseData.status} />
                  </div>
                  {caseData.description && (
                    <p className="text-gray-600 max-w-3xl">{caseData.description}</p>
                  )}
                  <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                    <span>Created {format(new Date(caseData.created_at), 'MMMM d, yyyy')}</span>
                    <span>•</span>
                    <span>Updated {format(new Date(caseData.updated_at), 'MMMM d, yyyy')}</span>
                    {caseData.document_count !== undefined && (
                      <>
                        <span>•</span>
                        <span>{caseData.document_count} documents</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => setIsEditing(true)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <PencilIcon className="h-4 w-4 mr-2" />
                    Edit
                  </button>

                  {caseData.status !== CaseStatus.ARCHIVED && (
                    <button
                      onClick={handleArchive}
                      disabled={updateCase.isPending}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                      <ArchiveBoxIcon className="h-4 w-4 mr-2" />
                      {updateCase.isPending ? 'Archiving...' : 'Archive'}
                    </button>
                  )}

                  <button
                    onClick={() => setShowDeleteDialog(true)}
                    className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
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
