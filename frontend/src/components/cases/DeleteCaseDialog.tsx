/**
 * DeleteCaseDialog Component
 * Confirmation dialog for deleting a case
 */

import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useDeleteCase } from '../../hooks/useCases';
import type { Case } from '../../types';

interface DeleteCaseDialogProps {
  case: Case | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function DeleteCaseDialog({ case: caseData, isOpen, onClose, onSuccess }: DeleteCaseDialogProps) {
  const deleteCase = useDeleteCase();

  const handleDelete = async () => {
    if (!caseData) return;

    try {
      await deleteCase.mutateAsync(caseData.id);
      onClose();

      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error('Failed to delete case:', error);
    }
  };

  if (!caseData) return null;

  const hasDocuments = (caseData.document_count || 0) > 0;

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <ExclamationTriangleIcon
                        className="h-6 w-6 text-red-600"
                        aria-hidden="true"
                      />
                    </div>
                    <Dialog.Title
                      as="h3"
                      className="ml-3 text-lg font-semibold text-gray-900"
                    >
                      Delete Case
                    </Dialog.Title>
                  </div>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-500 focus:outline-none"
                    disabled={deleteCase.isPending}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="mt-2">
                  <p className="text-sm text-gray-600 mb-3">
                    Are you sure you want to delete the case{' '}
                    <span className="font-semibold text-gray-900">"{caseData.name}"</span>?
                  </p>

                  {hasDocuments && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-3">
                      <p className="text-sm text-yellow-800">
                        <strong>Warning:</strong> This case contains{' '}
                        <strong>{caseData.document_count} document(s)</strong>. Deleting the case
                        will also delete all associated documents, chunks, embeddings, and
                        analyses.
                      </p>
                    </div>
                  )}

                  <p className="text-sm text-gray-600">
                    This action cannot be undone. All data associated with this case will be
                    permanently deleted from the database and vector store.
                  </p>
                </div>

                {deleteCase.isError && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-600">
                      Failed to delete case. Please try again or contact support if the problem
                      persists.
                    </p>
                  </div>
                )}

                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    disabled={deleteCase.isPending}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleDelete}
                    className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={deleteCase.isPending}
                  >
                    {deleteCase.isPending ? 'Deleting...' : 'Delete Case'}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
