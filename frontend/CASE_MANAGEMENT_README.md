# Case Management System - Quick Start Guide

## Overview

Complete Case Management system for the Investigation Intelligence Platform with Dashboard, CRUD operations, filtering, pagination, and real-time updates.

## Features

- **Dashboard**: Overview with stats cards and case list
- **Case CRUD**: Create, read, update, delete cases
- **Filtering**: Search by name, filter by status
- **Pagination**: Navigate large datasets efficiently
- **Responsive**: Mobile, tablet, and desktop layouts
- **Real-time**: Optimistic updates with React Query

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Ensure `VITE_API_BASE_URL` points to your backend:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. Start Development Server

```bash
npm run dev
```

Open http://localhost:5173

## Usage

### Creating a Case

1. Click "Create New Case" button on Dashboard
2. Fill in case name (required)
3. Optionally add description
4. Select status (default: Open)
5. Click "Create Case"

### Viewing Cases

- **Grid View**: Card-based layout (default)
- **Table View**: Sortable table with columns
- Toggle between views using the icons

### Filtering Cases

- **Search**: Type in search box to filter by name
- **Status**: Select status from dropdown
- **Clear**: Click "Clear Filters" to reset

### Editing a Case

**Option 1: From Dashboard**
1. Click case card or "Edit" button
2. Modify case details inline
3. Click "Save Changes"

**Option 2: From Case Details**
1. Navigate to case details page
2. Click "Edit" button in header
3. Update fields
4. Click "Save Changes"

### Deleting a Case

1. Click "Delete" in action menu or case details
2. Confirm deletion in dialog
3. Warning shown if case contains documents

### Viewing Case Details

1. Click on case card or "View Details"
2. See case header with metadata
3. View statistics (documents, success rate)
4. Browse tabs: Documents, Analysis, Activity

## Component Structure

```
src/
├── types/
│   └── index.ts          # TypeScript types
├── api/
│   ├── client.ts         # Axios HTTP client
│   └── cases.ts          # Case API functions
├── hooks/
│   └── useCases.ts       # React Query hooks
├── components/
│   ├── ui/               # Shared components
│   │   ├── StatusBadge.tsx
│   │   ├── LoadingSkeleton.tsx
│   │   └── ErrorMessage.tsx
│   └── cases/            # Case-specific components
│       ├── CaseCard.tsx
│       ├── CaseList.tsx
│       ├── CaseFilters.tsx
│       ├── CasePagination.tsx
│       ├── CreateCaseModal.tsx
│       ├── EditCaseForm.tsx
│       ├── DeleteCaseDialog.tsx
│       ├── CaseHeader.tsx
│       └── CaseStats.tsx
└── pages/
    ├── Dashboard.tsx     # Main page
    └── CaseDetails.tsx   # Case detail page
```

## API Integration

### Endpoints Used

- `GET /api/v1/cases` - List cases
- `GET /api/v1/cases/:id` - Get case
- `POST /api/v1/cases` - Create case
- `PUT /api/v1/cases/:id` - Update case
- `DELETE /api/v1/cases/:id` - Delete case
- `GET /api/v1/cases/:id/stats` - Case stats
- `GET /api/v1/cases/stats/dashboard` - Dashboard stats

### Request Examples

**Create Case:**
```typescript
{
  "name": "Acme Corp Investigation",
  "description": "Financial investigation for Q4 2023",
  "status": "open"
}
```

**Update Case:**
```typescript
{
  "name": "Acme Corp Investigation (Updated)",
  "status": "in_progress"
}
```

## Customization

### Changing Page Size

In `Dashboard.tsx`:

```typescript
const [filters, setFilters] = useState({
  page: 1,
  page_size: 12, // Change this value
});
```

### Modifying Status Options

In `src/types/index.ts`:

```typescript
export enum CaseStatus {
  OPEN = 'open',
  IN_PROGRESS = 'in_progress',
  // Add your custom statuses here
}
```

### Customizing Colors

Status colors in `StatusBadge.tsx`:

```typescript
const STATUS_STYLES = {
  [CaseStatus.OPEN]: 'bg-blue-100 text-blue-800',
  // Modify colors here
};
```

## Troubleshooting

### API Connection Issues

**Problem**: Cases not loading
**Solution**: Check `VITE_API_BASE_URL` in `.env` file

### TypeScript Errors

**Problem**: Type errors in components
**Solution**: Run `npm run type-check` to identify issues

### React Query Cache Issues

**Problem**: Stale data shown
**Solution**: Adjust `staleTime` in `useCases.ts` hooks

## Performance Tips

1. **Pagination**: Keep page size reasonable (12-20 items)
2. **Caching**: React Query caches for 30-60 seconds
3. **Optimistic Updates**: Enabled for mutations
4. **Lazy Loading**: Modals loaded on demand

## Accessibility

- Keyboard navigation supported
- ARIA labels on interactive elements
- Semantic HTML structure
- Color contrast meets WCAG AA

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS 12+, Android 8+)

## Next Steps

1. Test all CRUD operations
2. Customize styles to match brand
3. Add toast notifications (install `sonner`)
4. Integrate with Document Upload agent
5. Add analytics/tracking

## Support

For issues or questions:
1. Check CASE_MANAGEMENT_SUMMARY.md for details
2. Review API documentation in backend/
3. Check React Query DevTools in development

## License

Part of Investigation Intelligence Platform
