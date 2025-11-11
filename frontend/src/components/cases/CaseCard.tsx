/**
 * CaseCard Component
 * Card view for displaying a single case with action menu
 */

import { Link } from 'react-router-dom';
import { EllipsisVerticalIcon, DocumentTextIcon, CalendarIcon } from '@heroicons/react/24/outline';
import { Menu } from '@headlessui/react';
import { format } from 'date-fns';
import { StatusBadge } from '../ui/StatusBadge';
import type { Case } from '../../types';

interface CaseCardProps {
  case: Case;
  onEdit: (caseItem: Case) => void;
  onDelete: (caseItem: Case) => void;
  onArchive?: (caseItem: Case) => void;
}

export function CaseCard({ case: caseItem, onEdit, onDelete, onArchive }: CaseCardProps) {
  const truncateDescription = (text: string | undefined, maxLength: number = 120) => {
    if (!text) return 'No description';
    return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
  };

  return (
    <div className="bg-white border border-gray-200/60 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-blue-200/60 overflow-hidden group">
      <Link to={`/cases/${caseItem.id}`} className="block p-6">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-bold text-gray-900 group-hover:bg-gradient-to-r group-hover:from-blue-600 group-hover:to-purple-600 group-hover:bg-clip-text group-hover:text-transparent transition-all line-clamp-1">
            {caseItem.name}
          </h3>
          <StatusBadge status={caseItem.status} />
        </div>

        <p className="text-sm text-gray-600 mb-4 line-clamp-2 leading-relaxed">
          {truncateDescription(caseItem.description)}
        </p>

        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            <span className="flex items-center bg-blue-50 px-2 py-1 rounded-full">
              <DocumentTextIcon className="h-4 w-4 mr-1 text-blue-600" />
              <span className="font-medium text-gray-700">{caseItem.document_count || 0} docs</span>
            </span>
            <span className="flex items-center bg-purple-50 px-2 py-1 rounded-full">
              <CalendarIcon className="h-4 w-4 mr-1 text-purple-600" />
              <span className="font-medium text-gray-700">{format(new Date(caseItem.created_at), 'MMM d, yyyy')}</span>
            </span>
          </div>
        </div>
      </Link>

      {/* Action Menu */}
      <div className="border-t border-gray-100 px-6 py-3 bg-gradient-to-r from-gray-50 to-blue-50/30">
        <div className="flex items-center justify-between">
          <Link
            to={`/cases/${caseItem.id}`}
            className="text-sm font-semibold text-blue-600 hover:text-blue-700 hover:underline transition-all"
          >
            Szczegóły sprawy →
          </Link>

          <Menu as="div" className="relative">
            <Menu.Button className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100">
              <EllipsisVerticalIcon className="h-5 w-5" />
            </Menu.Button>

            <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
              <div className="py-1">
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        onEdit(caseItem);
                      }}
                      className={`${
                        active ? 'bg-gray-100' : ''
                      } block w-full text-left px-4 py-2 text-sm text-gray-700`}
                    >
                      Edit Case
                    </button>
                  )}
                </Menu.Item>

                {onArchive && caseItem.status !== 'archived' && (
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          onArchive(caseItem);
                        }}
                        className={`${
                          active ? 'bg-gray-100' : ''
                        } block w-full text-left px-4 py-2 text-sm text-gray-700`}
                      >
                        Archive Case
                      </button>
                    )}
                  </Menu.Item>
                )}

                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        onDelete(caseItem);
                      }}
                      className={`${
                        active ? 'bg-red-50' : ''
                      } block w-full text-left px-4 py-2 text-sm text-red-600`}
                    >
                      Delete Case
                    </button>
                  )}
                </Menu.Item>
              </div>
            </Menu.Items>
          </Menu>
        </div>
      </div>
    </div>
  );
}
