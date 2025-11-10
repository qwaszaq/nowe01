/**
 * CaseList Component
 * Displays cases in grid or table view
 */

import { useState } from 'react';
import { CaseCard } from './CaseCard';
import { StatusBadge } from '../ui/StatusBadge';
import { EmptyState } from '../ui/ErrorMessage';
import { Squares2X2Icon, ListBulletIcon, FolderIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import type { Case, ViewMode } from '../../types';

interface CaseListProps {
  cases: Case[];
  onEdit: (caseItem: Case) => void;
  onDelete: (caseItem: Case) => void;
  onArchive?: (caseItem: Case) => void;
  onCreate?: () => void;
}

export function CaseList({ cases, onEdit, onDelete, onArchive, onCreate }: CaseListProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');

  if (cases.length === 0) {
    return (
      <EmptyState
        title="No cases found"
        description="Get started by creating your first case to organize documents and analyses."
        icon={FolderIcon}
        action={
          onCreate
            ? {
                label: 'Create New Case',
                onClick: onCreate,
              }
            : undefined
        }
      />
    );
  }

  return (
    <div>
      {/* View Mode Toggle */}
      <div className="flex justify-end mb-4">
        <div className="inline-flex rounded-md shadow-sm" role="group">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-2 text-sm font-medium rounded-l-lg border ${
              viewMode === 'grid'
                ? 'bg-blue-50 text-blue-700 border-blue-200'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
            aria-label="Grid view"
          >
            <Squares2X2Icon className="h-5 w-5" />
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`px-3 py-2 text-sm font-medium rounded-r-lg border-t border-r border-b ${
              viewMode === 'table'
                ? 'bg-blue-50 text-blue-700 border-blue-200'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
            aria-label="Table view"
          >
            <ListBulletIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Grid View */}
      {viewMode === 'grid' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cases.map((caseItem) => (
            <CaseCard
              key={caseItem.id}
              case={caseItem}
              onEdit={onEdit}
              onDelete={onDelete}
              onArchive={onArchive}
            />
          ))}
        </div>
      )}

      {/* Table View */}
      {viewMode === 'table' && (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  Name
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  Status
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  Documents
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  Created
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {cases.map((caseItem) => (
                <tr key={caseItem.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{caseItem.name}</div>
                      {caseItem.description && (
                        <div className="text-sm text-gray-500 line-clamp-1">
                          {caseItem.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={caseItem.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {caseItem.document_count || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(caseItem.created_at), 'MMM d, yyyy')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button
                      onClick={() => onEdit(caseItem)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onDelete(caseItem)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
