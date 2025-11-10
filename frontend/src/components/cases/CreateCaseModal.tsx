/**
 * CreateCaseModal Component
 * Modal form for creating a new case
 */

import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useCreateCase } from '../../hooks/useCases';
import { CaseStatus, type CreateCaseRequest } from '../../types';
import { createCaseSchema } from '../../lib/validations';

interface CreateCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (caseId: string) => void;
}

export function CreateCaseModal({ isOpen, onClose, onSuccess }: CreateCaseModalProps) {
  const createCase = useCreateCase();

  const [formData, setFormData] = useState<CreateCaseRequest>({
    name: '',
    description: '',
    status: CaseStatus.OPEN,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    const nameError = createCaseSchema.name(formData.name);
    if (nameError !== true) {
      newErrors.name = nameError;
    }

    const descError = createCaseSchema.description(formData.description);
    if (descError !== true) {
      newErrors.description = descError;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    try {
      const newCase = await createCase.mutateAsync(formData);

      // Reset form
      setFormData({
        name: '',
        description: '',
        status: CaseStatus.OPEN,
      });
      setErrors({});

      // Close modal
      onClose();

      // Call success callback
      if (onSuccess) {
        onSuccess(newCase.id);
      }
    } catch (error) {
      console.error('Failed to create case:', error);
      setErrors({
        submit: error instanceof Error ? error.message : 'Failed to create case',
      });
    }
  };

  const handleClose = () => {
    if (!createCase.isPending) {
      setFormData({
        name: '',
        description: '',
        status: CaseStatus.OPEN,
      });
      setErrors({});
      onClose();
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
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
                <div className="flex items-center justify-between mb-4">
                  <Dialog.Title as="h3" className="text-lg font-semibold text-gray-900">
                    Create New Case
                  </Dialog.Title>
                  <button
                    onClick={handleClose}
                    className="text-gray-400 hover:text-gray-500 focus:outline-none"
                    disabled={createCase.isPending}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <form onSubmit={handleSubmit}>
                  {/* Case Name */}
                  <div className="mb-4">
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                      Case Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className={`block w-full rounded-md border ${
                        errors.name ? 'border-red-300' : 'border-gray-300'
                      } px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm`}
                      placeholder="Enter case name"
                      disabled={createCase.isPending}
                      maxLength={255}
                    />
                    {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
                  </div>

                  {/* Description */}
                  <div className="mb-4">
                    <label
                      htmlFor="description"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Description
                    </label>
                    <textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={4}
                      className={`block w-full rounded-md border ${
                        errors.description ? 'border-red-300' : 'border-gray-300'
                      } px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm`}
                      placeholder="Enter case description (optional)"
                      disabled={createCase.isPending}
                    />
                    {errors.description && (
                      <p className="mt-1 text-sm text-red-600">{errors.description}</p>
                    )}
                  </div>

                  {/* Status */}
                  <div className="mb-6">
                    <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <select
                      id="status"
                      value={formData.status}
                      onChange={(e) =>
                        setFormData({ ...formData, status: e.target.value as CaseStatus })
                      }
                      className="block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm"
                      disabled={createCase.isPending}
                    >
                      <option value={CaseStatus.OPEN}>Open</option>
                      <option value={CaseStatus.IN_PROGRESS}>In Progress</option>
                      <option value={CaseStatus.UNDER_REVIEW}>Under Review</option>
                      <option value={CaseStatus.COMPLETED}>Completed</option>
                      <option value={CaseStatus.ARCHIVED}>Archived</option>
                      <option value={CaseStatus.CLOSED}>Closed</option>
                    </select>
                  </div>

                  {/* Error Message */}
                  {errors.submit && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                      <p className="text-sm text-red-600">{errors.submit}</p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={handleClose}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      disabled={createCase.isPending}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={createCase.isPending}
                    >
                      {createCase.isPending ? 'Creating...' : 'Create Case'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
