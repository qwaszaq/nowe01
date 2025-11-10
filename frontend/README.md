# Investigation Intelligence Platform - Frontend

Modern React frontend application built with Vite, TypeScript, and Tailwind CSS for the Investigation Intelligence Platform.

## Technology Stack

- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type-safe development with strict mode
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router v6** - Client-side routing
- **React Query (TanStack Query)** - Data fetching, caching, and state management
- **Axios** - HTTP client for API communication
- **Headless UI** - Unstyled, accessible UI components
- **Heroicons** - Beautiful hand-crafted SVG icons
- **Recharts** - Composable charting library for data visualization
- **date-fns** - Modern JavaScript date utility library

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   └── ui/          # Base UI components (Button, Card, etc.)
│   ├── layouts/         # Layout components
│   │   └── MainLayout.tsx
│   ├── pages/           # Page components (routes)
│   │   ├── Dashboard.tsx
│   │   ├── CaseDetails.tsx
│   │   ├── DocumentDetails.tsx
│   │   └── AnalysisViewer.tsx
│   ├── lib/             # Utilities and configurations
│   │   ├── api.ts       # Axios configuration
│   │   ├── queryClient.ts  # React Query configuration
│   │   └── utils.ts     # Helper functions
│   ├── types/           # TypeScript type definitions
│   │   └── api.ts       # API types matching backend
│   ├── App.tsx          # Main app component with routes
│   ├── main.tsx         # Application entry point
│   └── index.css        # Global styles and Tailwind directives
├── public/              # Static assets
├── index.html           # HTML entry point
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript configuration
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
└── postcss.config.js    # PostCSS configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm (or yarn/pnpm)
- Backend API running at http://localhost:8000

### Installation

1. **Install dependencies:**

```bash
npm install
```

2. **Create environment file:**

```bash
cp .env.example .env
```

Edit `.env` if you need to change the API base URL:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Development

**Start the development server:**

```bash
npm run dev
```

The application will be available at http://localhost:3000

The dev server includes:
- Hot Module Replacement (HMR)
- Fast refresh for React components
- Proxy to backend API (avoids CORS issues)
- React Query DevTools

### Build

**Create production build:**

```bash
npm run build
```

**Preview production build:**

```bash
npm run preview
```

### Code Quality

**Type checking:**

```bash
npm run type-check
```

**Linting:**

```bash
npm run lint
```

## Configuration

### API Proxy

The Vite dev server is configured to proxy API requests to the backend:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

This means you can make requests to `/api/cases` and they'll be proxied to `http://localhost:8000/api/cases`.

### TypeScript

Strict mode is enabled for maximum type safety:

```json
{
  "strict": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true,
  "noFallthroughCasesInSwitch": true
}
```

Path aliases are configured for cleaner imports:

```typescript
import { api } from '@/lib/api';
import { Case } from '@/types/api';
```

### Tailwind CSS

Custom theme extends the default Tailwind configuration:

- **Primary color**: Blue palette (used for main actions)
- **Secondary color**: Purple palette (used for accents)
- **Font**: Inter (loaded from Google Fonts)

Custom utility classes are defined in `src/index.css`.

## React Query Configuration

React Query is configured with sensible defaults:

- **Stale time**: 5 minutes (data is fresh for 5 minutes)
- **Cache time**: 10 minutes (unused data stays in cache)
- **Retry**: 3 attempts with exponential backoff
- **Refetch on window focus**: Enabled
- **Refetch on reconnect**: Enabled

Query keys are managed through a centralized factory in `lib/queryClient.ts`:

```typescript
import { queryKeys } from '@/lib/queryClient';

// Use consistent query keys
useQuery({
  queryKey: queryKeys.cases.detail(caseId),
  queryFn: () => fetchCase(caseId),
});
```

## API Client

The API client (`lib/api.ts`) provides:

- Base URL configuration from environment
- Request/response interceptors
- Global error handling
- Authentication token injection (when implemented)
- Development logging
- Separate instance for file uploads with longer timeout

### Making API Calls

```typescript
import { api } from '@/lib/api';

// GET request
const response = await api.get('/api/cases');

// POST request
const response = await api.post('/api/cases', {
  name: 'New Case',
  description: 'Case description',
});

// File upload
import { uploadApi } from '@/lib/api';

const formData = new FormData();
formData.append('file', file);
const response = await uploadApi.post('/api/documents/upload', formData);
```

## Component Library

### Base UI Components

Located in `src/components/ui/`:

- **Button** - Multiple variants (primary, secondary, danger, ghost) and sizes
- **Card** - Container component with header, body, footer sections
- **Badge** - Status indicators with color variants
- **Spinner** - Loading indicator
- **Input** - Form input with error states
- **ErrorMessage** - Error display component
- **LoadingSkeleton** - Loading placeholder
- **StatusBadge** - Status-specific badge with colors

### Using Components

```typescript
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';

<Card>
  <Card.Header>
    <h2>Title</h2>
  </Card.Header>
  <Card.Body>
    <p>Content</p>
  </Card.Body>
  <Card.Footer>
    <Button variant="primary">Action</Button>
  </Card.Footer>
</Card>
```

## Routing

Routes are defined in `App.tsx`:

- `/` - Dashboard (case list)
- `/cases/:caseId` - Case details
- `/cases/:caseId/documents/:documentId` - Document details
- `/cases/:caseId/documents/:documentId/analysis` - Analysis viewer
- `/404` - Not found page

## TypeScript Types

All API types are defined in `src/types/api.ts` to match the backend Pydantic models:

- **Case** - Case entity
- **Document** - Document entity with processing status
- **AnalysisResult** - Financial analysis results
- **FinancialMetric** - Individual metric with citations
- **AnalysisInsights** - AI-generated insights
- **SearchResult** - Semantic search results
- **PaginatedResponse** - Paginated API responses

## Environment Variables

All environment variables must be prefixed with `VITE_`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Investigation Intelligence Platform
VITE_APP_VERSION=1.0.0
VITE_ENABLE_DEVTOOLS=true
VITE_ENABLE_QUERY_DEVTOOLS=true
```

Access in code:

```typescript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

## Development Tips

### React Query DevTools

In development, the React Query DevTools are available in the bottom-right corner. Use them to:
- Inspect cached queries
- See query states and updates
- Manually trigger refetches
- Debug stale/fresh data

### Hot Reload

Vite provides instant hot module replacement. Changes to:
- React components - fast refresh
- CSS/Tailwind - instant update
- TypeScript - type-checked on save

### Error Boundaries

The app is wrapped in an Error Boundary that catches and displays errors gracefully. In development, you'll see the full stack trace.

### Browser DevTools

Recommended extensions:
- React Developer Tools
- Redux DevTools (for React Query DevTools)

## Phase Implementation Plan

This is the base setup. Features will be implemented by specialized agents:

1. **Phase 5a** - Case Management (Dashboard, case list, create/edit cases)
2. **Phase 5b** - Document Upload (Upload UI, progress tracking, document list)
3. **Phase 5c** - Analysis Viewer (Display financial ratios, charts, insights)
4. **Phase 5d** - Integration Testing (E2E tests, backend integration)

## Troubleshooting

### Port Already in Use

If port 3000 is in use:

```bash
# Change port in package.json or use environment variable
PORT=3001 npm run dev
```

### API Connection Issues

1. Verify backend is running at http://localhost:8000
2. Check CORS settings on backend
3. Verify proxy configuration in `vite.config.ts`
4. Check browser console for network errors

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

## Contributing

When implementing new features:

1. Follow the existing project structure
2. Use TypeScript strict mode
3. Define types in `types/api.ts`
4. Use React Query for data fetching
5. Create reusable components in `components/ui/`
6. Follow Tailwind CSS conventions
7. Add error handling and loading states

## Resources

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Router](https://reactrouter.com/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Headless UI](https://headlessui.com/)

## License

Internal investigation platform - all rights reserved.
