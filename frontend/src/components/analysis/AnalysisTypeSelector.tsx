import React from 'react';
import { AnalysisType, ANALYSIS_TYPE_LABELS, ANALYSIS_TYPE_DESCRIPTIONS } from '../../types/analysis';
import { clsx } from 'clsx';

interface AnalysisTypeSelectorProps {
  value: AnalysisType;
  onChange: (type: AnalysisType) => void;
  className?: string;
}

const analysisTypes: AnalysisType[] = [
  'comprehensive',
  'liquidity',
  'profitability',
  'leverage',
  'quick'
];

export const AnalysisTypeSelector: React.FC<AnalysisTypeSelectorProps> = ({
  value,
  onChange,
  className = ''
}) => {
  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-2 ${className}`}>
      <div className="flex flex-wrap gap-2">
        {analysisTypes.map((type) => {
          const isActive = value === type;
          return (
            <button
              key={type}
              onClick={() => onChange(type)}
              className={clsx(
                'flex-1 min-w-[140px] px-4 py-3 rounded-md text-sm font-medium transition-all',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                isActive
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
              )}
            >
              <div className="text-left">
                <div className="font-semibold">{ANALYSIS_TYPE_LABELS[type]}</div>
                <div
                  className={clsx(
                    'text-xs mt-1',
                    isActive ? 'text-blue-100' : 'text-gray-500'
                  )}
                >
                  {ANALYSIS_TYPE_DESCRIPTIONS[type]}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
