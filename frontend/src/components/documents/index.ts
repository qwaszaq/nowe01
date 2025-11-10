/**
 * Document Components
 * Export all document-related components for easy importing
 */

export { DocumentStatusBadge, isProcessingStatus, isFinalStatus, getStatusProgress, getStageDescription } from './DocumentStatusBadge';
export type { DocumentStatus } from './DocumentStatusBadge';

export { DropZone, FilePreview } from './DropZone';

export { UploadProgress } from './UploadProgress';
export type { FileUploadProgress } from './UploadProgress';

export { ProcessingTimeline, CompactProcessingTimeline } from './ProcessingTimeline';
export type { ProcessingStage } from './ProcessingTimeline';

export { DocumentStatusCard } from './DocumentStatusCard';
export type { DocumentStatusData } from './DocumentStatusCard';

export { DocumentUpload } from './DocumentUpload';

export { DocumentList } from './DocumentList';
export type { Document } from './DocumentList';

export { UploadModal, UploadButton } from './UploadModal';
