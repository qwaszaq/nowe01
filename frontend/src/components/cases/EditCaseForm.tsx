/**
 * EditCaseForm Component
 * Inline form for editing an existing case
 */

import { useState, useEffect } from 'react';
import { useUpdateCase } from '../../hooks/useCases';
import { CaseStatus, type Case, type UpdateCaseRequest } from '../../types';
import { updateCaseSchema } from '../../lib/validations';

interface EditCaseFormProps {
  case: Case;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function EditCaseForm({ case: caseData, onSuccess, onCancel }: EditCaseFormProps) {
  const updateCase = useUpdateCase();

  const [formData, setFormData] = useState<UpdateCaseRequest>({
    name: caseData.name,
    description: caseData.description || '',
    status: caseData.status,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset form when case changes
  useEffect(() => {
    setFormData({
      name: caseData.name,
      description: caseData.description || '',
      status: caseData.status,
    });
    setErrors({});
  }, [caseData]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (formData.name) {
      const nameError = updateCaseSchema.name(formData.name);
      if (nameError !== true) {
        newErrors.name = nameError;
      }
    }

    if (formData.description) {
      const descError = updateCaseSchema.description(formData.description);
      if (descError !== true) {
        newErrors.description = descError;
      }
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
      await updateCase.mutateAsync({
        caseId: caseData.id,
        request: formData,
      });

      setErrors({});

      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error('Failed to update case:', error);
      setErrors({
        submit: error instanceof Error ? error.message : 'Failed to update case',
      });
    }
  };

  const handleCancel = () => {
    setFormData({
      name: caseData.name,
      description: caseData.description || '',
      status: caseData.status,
    });
    setErrors({});

    if (onCancel) {
      onCancel();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Case Name */}
      <div>
        <label htmlFor="edit-name" className="block text-sm font-medium text-gray-700 mb-1">
          Case Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="edit-name"
          value={formData.name || ''}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className={`block w-full rounded-md border ${
            errors.name ? 'border-red-300' : 'border-gray-300'
          } px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm`}
          placeholder="Enter case name"
          disabled={updateCase.isPending}
          maxLength={255}
        />
        {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
      </div>

      {/* Description */}
      <div>
        <label htmlFor="edit-description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          id="edit-description"
          value={formData.description || ''}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          rows={4}
          className={`block w-full rounded-md border ${
            errors.description ? 'border-red-300' : 'border-gray-300'
          } px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm`}
          placeholder="Enter case description (optional)"
          disabled={updateCase.isPending}
        />
        {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description}</p>}
      </div>

      {/* Status */}
      <div>
        <label htmlFor="edit-status" className="block text-sm font-medium text-gray-700 mb-1">
          Status
        </label>
        <select
          id="edit-status"
          value={formData.status}
          onChange={(e) => setFormData({ ...formData, status: e.target.value as CaseStatus })}
          className="block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm"
          disabled={updateCase.isPending}
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
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{errors.submit}</p>
        </div>
      )}

      {/* Success Message */}
      {updateCase.isSuccess && !errors.submit && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-sm text-green-600">Case updated successfully!</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end space-x-3 pt-2">
        <button
          type="button"
          onClick={handleCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          disabled={updateCase.isPending}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={updateCase.isPending}
        >
          {updateCase.isPending ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
}
