import React, { useState, useRef, useEffect } from 'react';
import { useExportAnalysis } from '../../hooks/useAnalysis';
import { AnalysisType } from '../../types/analysis';
import { Button } from '../ui/Button';

interface ExportMenuProps {
  documentId: string;
  analysisType: AnalysisType;
  className?: string;
}

export const ExportMenu: React.FC<ExportMenuProps> = ({
  documentId,
  analysisType,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const exportMutation = useExportAnalysis();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleExport = async (format: 'pdf' | 'excel' | 'json') => {
    try {
      const result = await exportMutation.mutateAsync({
        documentId,
        analysisType,
        format
      });

      // Download the file
      if (format === 'json') {
        // JSON data - create blob and download
        const blob = new Blob([JSON.stringify(result.data, null, 2)], {
          type: 'application/json'
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `analysis-${documentId}-${analysisType}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        // PDF or Excel - blob data
        const blob = new Blob([result.data], {
          type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `analysis-${documentId}-${analysisType}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }

      setIsOpen(false);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleEmailReport = () => {
    const subject = encodeURIComponent(`Financial Analysis Report - ${analysisType}`);
    const body = encodeURIComponent(
      `Please find attached the financial analysis report.\n\nDocument ID: ${documentId}\nAnalysis Type: ${analysisType}`
    );
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`} ref={menuRef}>
      <Button
        onClick={() => setIsOpen(!isOpen)}
        variant="outline"
        leftIcon={
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        }
        rightIcon={
          <svg
            className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        }
      >
        Export
      </Button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
          <div className="py-1">
            {/* PDF Export */}
            <button
              onClick={() => handleExport('pdf')}
              disabled={exportMutation.isPending}
              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
                className="w-5 h-5 mr-3 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
              <div>
                <div className="font-medium">Export as PDF</div>
                <div className="text-xs text-gray-500">Formatted report</div>
              </div>
            </button>

            {/* Excel Export */}
            <button
              onClick={() => handleExport('excel')}
              disabled={exportMutation.isPending}
              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
                className="w-5 h-5 mr-3 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <div>
                <div className="font-medium">Export as Excel</div>
                <div className="text-xs text-gray-500">Raw data spreadsheet</div>
              </div>
            </button>

            {/* JSON Export */}
            <button
              onClick={() => handleExport('json')}
              disabled={exportMutation.isPending}
              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
                className="w-5 h-5 mr-3 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                />
              </svg>
              <div>
                <div className="font-medium">Export as JSON</div>
                <div className="text-xs text-gray-500">API response data</div>
              </div>
            </button>

            <div className="border-t border-gray-200 my-1" />

            {/* Email Report */}
            <button
              onClick={handleEmailReport}
              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
            >
              <svg
                className="w-5 h-5 mr-3 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <div>
                <div className="font-medium">Email Report</div>
                <div className="text-xs text-gray-500">Open email client</div>
              </div>
            </button>
          </div>

          {exportMutation.isPending && (
            <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center text-sm text-gray-600">
                <svg
                  className="animate-spin h-4 w-4 mr-2"
                  xmlns="http://www.w3.org/2000/svg"
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
                Exporting...
              </div>
            </div>
          )}

          {exportMutation.isError && (
            <div className="px-4 py-2 border-t border-gray-200 bg-red-50">
              <p className="text-xs text-red-600">
                Export failed. Please try again.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
