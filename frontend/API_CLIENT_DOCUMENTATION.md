# API Client Layer Documentation

**Phase 5 - React Query Integration Complete**

This document provides a comprehensive guide to the API client layer with React Query hooks for the Investigation Intelligence Platform.

## Table of Contents

- [Overview](#overview)
- [Files Created](#files-created)
- [Architecture](#architecture)
- [Usage Guide](#usage-guide)
- [API Services](#api-services)
- [React Query Hooks](#react-query-hooks)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Overview

The API client layer provides:

- **Type-safe API calls** with full TypeScript support
- **Automatic caching** with React Query
- **Optimistic updates** for mutations
- **Query invalidation** on data changes
- **Real-time polling** for document processing status
- **File upload progress** tracking
- **Comprehensive error handling**

### Tech Stack

- **Axios**: HTTP client with interceptors
- **React Query v5**: Data fetching and caching
- **TypeScript**: Full type safety
- **Path aliases**: `@/` for clean imports

---

## Files Created

### Core Configuration (3 files, 456 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `src/lib/api.ts` | 200 | Axios client with interceptors |
| `src/types/api.ts` | 256 | TypeScript types for all API operations |
| `src/lib/errorHandling.ts` | 378 | Error parsing and user-friendly messages |

### API Services (4 files, 485 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `src/services/api/casesApi.ts` | 115 | Case CRUD operations |
| `src/services/api/documentsApi.ts` | 162 | Document upload and management |
| `src/services/api/analysisApi.ts` | 192 | Analysis and semantic search |
| `src/services/api/index.ts` | 8 | Service exports |

### React Query Hooks (3 files, 815 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `src/hooks/useCases.ts` | 183 | Case query and mutation hooks |
| `src/hooks/useDocuments.ts` | 403 | Document upload, status polling hooks |
| `src/hooks/useAnalysis.ts` | 229 | Analysis and search hooks |

**Total: 10 files, ~1,756 lines of code**

---

## Architecture

```
frontend/src/
├── lib/
│   ├── api.ts                    # Axios client configuration
│   └── errorHandling.ts          # Error utilities
├── types/
│   └── api.ts                    # TypeScript types
├── services/api/
│   ├── casesApi.ts               # Cases service
│   ├── documentsApi.ts           # Documents service
│   ├── analysisApi.ts            # Analysis service
│   └── index.ts                  # Exports
└── hooks/
    ├── useCases.ts               # Cases hooks
    ├── useDocuments.ts           # Documents hooks
    └── useAnalysis.ts            # Analysis hooks
```

### Data Flow

```
Component → React Query Hook → API Service → Axios → Backend
                ↓
          React Query Cache
```

---

## Usage Guide

### 1. Setup Environment Variables

Create `.env` file:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### 2. Import Hooks

```tsx
import { useCases, useCreateCase } from '@/hooks/useCases';
import { useUploadDocument, useDocumentStatus } from '@/hooks/useDocuments';
import { useRunAnalysis, useSemanticSearch } from '@/hooks/useAnalysis';
```

### 3. Basic Example

```tsx
function CasesList() {
  const { data, isLoading, error } = useCases({ page: 1, status: 'active' });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Total Cases: {data.total}</h2>
      {data.cases?.map(case => (
        <div key={case.id}>{case.name}</div>
      ))}
    </div>
  );
}
```

---

## API Services

### casesApi

All case management operations.

#### Methods

```typescript
// List cases with pagination
casesApi.list(params?: { page?: number; page_size?: number; status?: string })

// Create new case
casesApi.create(data: { name: string; description?: string })

// Get case by ID
casesApi.get(caseId: string)

// Update case
casesApi.update(caseId: string, updates: { name?: string; description?: string; status?: string })

// Delete case (soft delete)
casesApi.delete(caseId: string)

// Get case statistics
casesApi.getStats(caseId: string)
```

#### Example

```typescript
import { casesApi } from '@/services/api/casesApi';

// Create a case
const newCase = await casesApi.create({
  name: 'Financial Fraud Investigation 2024-Q1',
  description: 'Investigation into suspected irregularities'
});

// Get stats
const stats = await casesApi.getStats(newCase.id);
console.log(`Success rate: ${stats.success_rate}%`);
```

---

### documentsApi

Document upload, management, and status tracking.

#### Methods

```typescript
// Upload document with progress tracking
documentsApi.upload(
  caseId: string,
  file: File,
  onProgress?: (progress: { percentage: number }) => void
)

// Get processing status
documentsApi.getStatus(documentId: string)

// List documents
documentsApi.list(params?: { case_id?: string; status?: string; page?: number })

// Get document by ID
documentsApi.get(documentId: string)

// Delete document
documentsApi.delete(documentId: string)

// Reprocess failed document
documentsApi.reprocess(documentId: string)
```

#### Example

```typescript
import { documentsApi } from '@/services/api/documentsApi';

// Upload with progress
const result = await documentsApi.upload(
  caseId,
  file,
  (progress) => console.log(`Upload: ${progress.percentage}%`)
);

// Poll status
const status = await documentsApi.getStatus(result.document_id);
console.log(`State: ${status.state}, Progress: ${status.progress_percent}%`);
```

---

### analysisApi

Financial analysis, semantic search, metrics, and insights.

#### Methods

```typescript
// Run financial analysis
analysisApi.analyze(request: {
  document_id: string;
  analysis_type: 'comprehensive' | 'liquidity' | 'profitability' | 'leverage' | 'quick';
})

// Get cached analysis
analysisApi.getCached(documentId: string, analysisType?: string)

// Semantic search
analysisApi.search(request: {
  case_id?: string;
  query: string;
  limit?: number;
  context_window?: number;
})

// Get metrics only
analysisApi.getMetrics(documentId: string, metricNames?: string[])

// Get insights only
analysisApi.getInsights(documentId: string)
```

#### Example

```typescript
import { analysisApi } from '@/services/api/analysisApi';

// Run comprehensive analysis
const result = await analysisApi.analyze({
  document_id: docId,
  analysis_type: 'comprehensive'
});

console.log('Quality Score:', result.quality_score);
console.log('Metrics:', result.metrics.length);
console.log('Overall Health:', result.insights.overall_health);

// Semantic search
const searchResults = await analysisApi.search({
  case_id: caseId,
  query: 'What is the revenue growth?',
  limit: 10
});
```

---

## React Query Hooks

### useCases

Query and mutation hooks for case management.

#### Query Hooks

```typescript
// List cases
const { data, isLoading, error } = useCases({ page: 1, status: 'active' });

// Get single case
const { data: case } = useCase(caseId);

// Get case stats
const { data: stats } = useCaseStats(caseId);
```

#### Mutation Hooks

```typescript
// Create case
const createCase = useCreateCase();
await createCase.mutateAsync({ name: 'New Case' });

// Update case
const updateCase = useUpdateCase(caseId);
await updateCase.mutateAsync({ name: 'Updated Name' });

// Delete case
const deleteCase = useDeleteCase();
await deleteCase.mutateAsync(caseId);
```

#### Full Example

```tsx
function CreateCaseForm() {
  const createCase = useCreateCase();
  const [name, setName] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const newCase = await createCase.mutateAsync({ name });
      console.log('Created:', newCase.id);
      // Navigate to case detail page
    } catch (error) {
      console.error('Failed:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
      />
      <button type="submit" disabled={createCase.isPending}>
        {createCase.isPending ? 'Creating...' : 'Create Case'}
      </button>
    </form>
  );
}
```

---

### useDocuments

Query and mutation hooks for document management with upload progress.

#### Query Hooks

```typescript
// List documents
const { data } = useDocuments({ case_id: caseId, page: 1 });

// Get single document
const { data: doc } = useDocument(documentId);

// Get processing status (auto-polls every 2s while processing)
const { data: status } = useDocumentStatus(documentId);
```

#### Mutation Hooks

```typescript
// Upload document
const uploadDocument = useUploadDocument();
await uploadDocument.mutateAsync({
  caseId,
  file,
  onProgress: (progress) => console.log(`${progress.percentage}%`)
});

// Delete document
const deleteDocument = useDeleteDocument();
await deleteDocument.mutateAsync(documentId);

// Reprocess failed document
const reprocess = useReprocessDocument();
await reprocess.mutateAsync(documentId);
```

#### Smart Upload Example

```tsx
function DocumentUpload({ caseId }: { caseId: string }) {
  const {
    upload,
    uploadProgress,
    isUploading,
    uploadedDocumentId,
    processingStatus,
  } = useDocumentUploadWithStatus(caseId);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload(file);
  };

  return (
    <div>
      <input type="file" accept=".pdf" onChange={handleFileChange} />

      {isUploading && (
        <div>Uploading: {uploadProgress}%</div>
      )}

      {uploadedDocumentId && processingStatus && (
        <div>
          <h3>Processing Document</h3>
          <div>Status: {processingStatus.state}</div>
          <div>Progress: {processingStatus.progress_percent}%</div>
        </div>
      )}
    </div>
  );
}
```

---

### useAnalysis

Query and mutation hooks for financial analysis and search.

#### Query Hooks

```typescript
// Get cached analysis result
const { data: result } = useAnalysisResult(documentId, 'comprehensive');

// Get metrics only
const { data: metrics } = useMetrics(documentId, ['current_ratio', 'roe']);

// Get insights only
const { data: insights } = useInsights(documentId);
```

#### Mutation Hooks

```typescript
// Run analysis
const runAnalysis = useRunAnalysis();
const result = await runAnalysis.mutateAsync({
  document_id: documentId,
  analysis_type: 'comprehensive'
});

// Semantic search
const search = useSemanticSearch();
const results = await search.mutateAsync({
  case_id: caseId,
  query: 'revenue growth',
  limit: 10
});
```

#### Full Example

```tsx
function AnalysisPanel({ documentId }: { documentId: string }) {
  const runAnalysis = useRunAnalysis();
  const { data: result } = useAnalysisResult(documentId, 'comprehensive');

  const handleAnalyze = async () => {
    await runAnalysis.mutateAsync({
      document_id: documentId,
      analysis_type: 'comprehensive'
    });
  };

  return (
    <div>
      <button onClick={handleAnalyze} disabled={runAnalysis.isPending}>
        {runAnalysis.isPending ? 'Analyzing...' : 'Run Analysis'}
      </button>

      {result && (
        <div>
          <h2>Quality Score: {result.quality_score}%</h2>
          <h3>Metrics ({result.metrics.length})</h3>
          {result.metrics.map(m => (
            <div key={m.metric_name}>
              {m.metric_name}: {m.metric_value} {m.metric_unit}
            </div>
          ))}

          <h3>Insights</h3>
          <div>Overall Health: {result.insights.overall_health}</div>
          <div>Risk: {result.insights.risk_assessment}</div>
        </div>
      )}
    </div>
  );
}
```

---

## Error Handling

### Error Utilities

```typescript
import {
  getErrorMessage,
  getErrorDetails,
  isNetworkError,
  isValidationError,
  formatValidationErrors,
} from '@/lib/errorHandling';
```

### Usage Examples

```tsx
// Basic error message
try {
  await casesApi.create({ name: '' });
} catch (error) {
  const message = getErrorMessage(error);
  toast.error(message); // "Case name cannot be empty"
}

// Detailed error info
try {
  await uploadDocument.mutateAsync({ caseId, file });
} catch (error) {
  const details = getErrorDetails(error);
  console.error({
    message: details.message,
    status: details.status,
    url: details.url,
  });
}

// Validation errors
try {
  await casesApi.update(caseId, { name: '' });
} catch (error) {
  if (isValidationError(error)) {
    const message = formatValidationErrors(error);
    toast.error(message);
  }
}

// Network errors
try {
  await casesApi.list();
} catch (error) {
  if (isNetworkError(error)) {
    toast.error('Network error. Check your connection.');
  }
}
```

---

## Best Practices

### 1. Query Keys

Use the provided query key factories for consistency:

```typescript
import { caseKeys } from '@/hooks/useCases';
import { documentKeys } from '@/hooks/useDocuments';
import { analysisKeys } from '@/hooks/useAnalysis';

// Invalidate specific queries
queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
queryClient.invalidateQueries({ queryKey: documentKeys.detail(docId) });
```

### 2. Optimistic Updates

Mutations automatically update the cache optimistically:

```typescript
// This automatically updates the UI before the server responds
const updateCase = useUpdateCase(caseId);
await updateCase.mutateAsync({ name: 'New Name' });
// UI updates immediately, rollback on error
```

### 3. Automatic Polling

Document status automatically polls while processing:

```typescript
// Auto-polls every 2 seconds until completed or failed
const { data: status } = useDocumentStatus(documentId);
```

### 4. Error Handling

Always handle errors in mutations:

```tsx
const createCase = useCreateCase();

const handleSubmit = async (data) => {
  try {
    await createCase.mutateAsync(data);
    toast.success('Case created!');
  } catch (error) {
    toast.error(getErrorMessage(error));
  }
};
```

### 5. Loading States

Use built-in loading states:

```tsx
const { data, isLoading, isFetching } = useCases();

if (isLoading) return <Spinner />;
if (isFetching) return <RefreshingIndicator />;
```

### 6. Stale Time

Query hooks have sensible stale times:

- Cases: 5 minutes
- Documents: 30 seconds
- Document status: 2 seconds (auto-polling)
- Analysis results: 1 hour (server-cached)

Override if needed:

```typescript
const { data } = useCases(
  { page: 1 },
  { staleTime: 1000 * 60 * 10 } // 10 minutes
);
```

---

## Summary for Other Agents

### Files Created

**10 files, ~1,756 lines of code**

1. `src/lib/api.ts` - Axios client with interceptors
2. `src/lib/errorHandling.ts` - Error utilities
3. `src/types/api.ts` - Complete TypeScript types
4. `src/services/api/casesApi.ts` - Cases service
5. `src/services/api/documentsApi.ts` - Documents service
6. `src/services/api/analysisApi.ts` - Analysis service
7. `src/services/api/index.ts` - Service exports
8. `src/hooks/useCases.ts` - Cases hooks
9. `src/hooks/useDocuments.ts` - Documents hooks (with upload progress)
10. `src/hooks/useAnalysis.ts` - Analysis hooks

### How to Use

Import hooks and use in components:

```tsx
import { useCases, useCreateCase } from '@/hooks/useCases';
import { useUploadDocument, useDocumentStatus } from '@/hooks/useDocuments';
import { useRunAnalysis } from '@/hooks/useAnalysis';
```

### Key Features

- **Type-safe**: Full TypeScript support
- **Auto-caching**: React Query handles all caching
- **Auto-polling**: Document status polls automatically
- **Upload progress**: Track file upload progress
- **Optimistic updates**: UI updates immediately
- **Error handling**: User-friendly error messages
- **Zero config**: Works out of the box

### Environment Setup

Add to `.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Next Steps for UI Agents

You can now build components using these hooks. Examples:

1. **Case List Page**: Use `useCases()`
2. **Case Detail Page**: Use `useCase(caseId)` and `useCaseStats(caseId)`
3. **Document Upload**: Use `useUploadDocument()` with progress
4. **Document Status**: Use `useDocumentStatus(docId)` for real-time updates
5. **Analysis Dashboard**: Use `useRunAnalysis()` and `useAnalysisResult()`
6. **Search Interface**: Use `useSemanticSearch()`

All hooks return standard React Query responses: `{ data, isLoading, error, refetch, ... }`

---

**API Client Layer Complete** ✅
