import React from 'react';
import { Citation } from '../../types/analysis';

interface CitationLinkProps {
  citation: Citation;
  onClick?: (citation: Citation) => void;
  className?: string;
}

export const CitationLink: React.FC<CitationLinkProps> = ({
  citation,
  onClick,
  className = ''
}) => {
  const handleClick = () => {
    if (onClick) {
      onClick(citation);
    } else {
      // Default behavior: open document viewer at specific page
      window.open(
        `/documents/${citation.document_id}?page=${citation.page}`,
        '_blank'
      );
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 transition-colors ${className}`}
      title={`${citation.document_name} - Page ${citation.page}`}
    >
      <svg
        className="w-3 h-3"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <span>Page {citation.page}</span>
    </button>
  );
};

interface CitationListProps {
  citations: Citation[];
  onClick?: (citation: Citation) => void;
  className?: string;
}

export const CitationList: React.FC<CitationListProps> = ({
  citations,
  onClick,
  className = ''
}) => {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {citations.map((citation, index) => (
        <CitationLink
          key={`${citation.document_id}-${citation.page}-${index}`}
          citation={citation}
          onClick={onClick}
        />
      ))}
    </div>
  );
};
