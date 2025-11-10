# Analysis Viewer System Documentation

## Overview

The Analysis Viewer is a comprehensive React/TypeScript system for displaying financial analysis results with interactive charts, metrics tables, AI insights, and semantic search capabilities. Built with modern tools including React Query, Recharts, and Tailwind CSS.

## Architecture

### Core Components

#### 1. **AnalysisPage** (`/frontend/src/pages/AnalysisPage.tsx`) - 246 lines
Main page component that orchestrates the entire analysis experience.

**Features:**
- Route: `/cases/:caseId/documents/:documentId/analysis`
- Analysis type selection (comprehensive, liquidity, profitability, leverage, quick)
- Run/refresh analysis controls
- Progress tracking during analysis
- Analysis history toggle
- Semantic search integration
- Error handling and loading states

**Key Functionality:**
```typescript
// Usage example
<AnalysisPage />
// Automatically reads caseId and documentId from route params
```

#### 2. **AnalysisResults** (`/frontend/src/components/analysis/AnalysisResults.tsx`) - 241 lines
Main results display component with three view modes.

**Features:**
- Quality score card display
- Three view modes: Grid, Table, Charts
- Export menu integration
- Summary statistics
- Responsive grid layout
- Citation tracking

**Props:**
```typescript
interface AnalysisResultsProps {
  data: AnalysisResult;
  onCitationClick?: (citation: any) => void;
  className?: string;
}
```

#### 3. **QualityScoreCard** (`/frontend/src/components/analysis/QualityScoreCard.tsx`) - 122 lines
Displays quality score with circular progress indicator.

**Features:**
- Circular progress chart using Recharts
- Color-coded quality levels (Excellent, Good, Fair, Poor)
- Score interpretation
- Quality scale legend
- Detailed explanation

**Quality Score Ranges:**
- 80-100: Excellent (Green)
- 60-79: Good (Blue)
- 40-59: Fair (Yellow)
- 0-39: Poor (Red)

#### 4. **MetricsTable** (`/frontend/src/components/analysis/MetricsTable.tsx`) - 259 lines
Interactive table for displaying financial metrics.

**Features:**
- Grouped by category (Liquidity, Profitability, Leverage)
- Sortable columns (Name, Value, Status)
- Expandable rows with detailed information
- Status indicators (Good, Warning, Poor)
- Citation links
- Color-coded status badges

#### 5. **MetricsCharts** (`/frontend/src/components/analysis/MetricsCharts.tsx`) - 289 lines
Data visualization using Recharts library.

**Chart Types:**
- **Bar Chart**: Compare ratios within categories
- **Line Chart**: Trend visualization
- **Radar Chart**: Multi-dimensional overview

**Features:**
- Interactive tooltips
- Category-based grouping
- Color-coded by metric status
- Responsive design
- Chart type toggle

#### 6. **MetricCard** (`/frontend/src/components/analysis/MetricCard.tsx`) - 124 lines
Individual metric display card.

**Features:**
- Large value display
- Status badge with color coding
- Interpretation text
- Citation links
- Expandable details
- Hover effects

#### 7. **InsightsPanel** (`/frontend/src/components/analysis/InsightsPanel.tsx`) - 212 lines
AI-generated insights display.

**Insight Categories:**
- Risk Assessment (Red theme)
- Liquidity Position (Blue theme)
- Financial Health (Green theme)
- Recommendations (Yellow theme)

**Features:**
- Category icons and color coding
- Severity badges (Low, Medium, High)
- Supporting metrics
- Citation sources
- Expandable content

#### 8. **SemanticSearch** (`/frontend/src/components/analysis/SemanticSearch.tsx`) - 207 lines
Natural language search interface.

**Features:**
- Natural language query input
- Example query chips
- Real-time search
- Loading and error states
- Results display
- Query history

**Example Queries:**
- "What is the revenue growth trend?"
- "How has debt changed over time?"
- "What are the main expenses?"
- "Describe the cash flow situation"
- "What are the key financial risks?"
- "Summarize the liquidity position"

#### 9. **SearchResults** (`/frontend/src/components/analysis/SearchResults.tsx`) - 247 lines
Search results display with highlighting.

**Features:**
- Relevance score visualization
- Query term highlighting
- Sort by relevance or page number
- Pagination (10 results per page)
- Click to view in context
- Metadata display

#### 10. **AnalysisTypeSelector** (`/frontend/src/components/analysis/AnalysisTypeSelector.tsx`) - 58 lines
Analysis type selection component.

**Analysis Types:**
1. **Comprehensive**: All 19 ratios + AI insights
2. **Liquidity**: 5 liquidity ratios
3. **Profitability**: 8 profitability ratios
4. **Leverage**: 6 leverage ratios
5. **Quick**: Fast overview with key metrics only

#### 11. **ExportMenu** (`/frontend/src/components/analysis/ExportMenu.tsx`) - 263 lines
Export functionality dropdown.

**Export Formats:**
- **PDF**: Formatted report
- **Excel**: Raw data spreadsheet
- **JSON**: API response data
- **Email**: Open email client with report details

#### 12. **AnalysisHistory** (`/frontend/src/components/analysis/AnalysisHistory.tsx`) - 270 lines
Historical analysis tracking.

**Features:**
- Timeline of past analyses
- Quality score comparison
- Trend indicators
- View/Compare actions
- Time since analysis

#### 13. **CitationLink** (`/frontend/src/components/analysis/CitationLink.tsx`) - 77 lines
Citation badge component.

**Features:**
- Document page reference
- Click to open at specific page
- Hover tooltip with document name
- Multiple citation support

### Utility Libraries

#### 14. **metricInterpretation.ts** (`/frontend/src/lib/metricInterpretation.ts`) - 328 lines
Financial ratio interpretation logic.

**Functions:**
- `interpretRatio()`: Interprets 19 financial ratios
- `interpretQualityScore()`: Quality score interpretation
- `formatMetricValue()`: Value formatting (%, x, etc.)
- `getStatusColor()`: Color class for status
- `getStatusIcon()`: Icon for status

**Supported Ratios:**

**Liquidity Ratios (5):**
1. Current Ratio
2. Quick Ratio
3. Cash Ratio
4. Working Capital Ratio
5. Operating Cash Flow Ratio

**Profitability Ratios (8):**
1. Gross Profit Margin
2. Operating Profit Margin
3. Net Profit Margin
4. Return on Assets (ROA)
5. Return on Equity (ROE)
6. Return on Investment (ROI)
7. EBITDA Margin
8. Operating Ratio

**Leverage Ratios (6):**
1. Debt-to-Equity Ratio
2. Debt-to-Assets Ratio
3. Equity Multiplier
4. Interest Coverage Ratio
5. Debt Service Coverage Ratio
6. Long-term Debt to Capitalization

### API Hooks

#### 15. **useAnalysis.ts** (`/frontend/src/hooks/useAnalysis.ts`) - 229 lines
React Query hooks for analysis operations.

**Hooks:**
- `useAnalysis()`: Fetch cached analysis
- `useRunAnalysis()`: Trigger new analysis
- `useAnalysisHistory()`: Fetch past analyses
- `useExportAnalysis()`: Export analysis data

**Usage:**
```typescript
// Fetch analysis
const { data, isLoading } = useAnalysis(documentId, 'comprehensive');

// Run analysis
const runAnalysis = useRunAnalysis();
await runAnalysis.mutateAsync({
  documentId,
  analysisType: 'comprehensive',
  forceRefresh: true
});

// Export
const exportMutation = useExportAnalysis();
await exportMutation.mutateAsync({
  documentId,
  analysisType: 'comprehensive',
  format: 'pdf'
});
```

#### 16. **useSemanticSearch.ts** (`/frontend/src/hooks/useSemanticSearch.ts`) - 86 lines
Semantic search mutation hook.

**Usage:**
```typescript
const search = useSemanticSearch();
const results = await search.mutateAsync({
  caseId,
  query: 'What is the revenue growth trend?',
  limit: 10,
  minScore: 0.5
});
```

### Type Definitions

#### 17. **analysis.ts** (`/frontend/src/types/analysis.ts`) - 102 lines
TypeScript type definitions.

**Main Types:**
```typescript
export type AnalysisType = 'comprehensive' | 'liquidity' | 'profitability' | 'leverage' | 'quick';
export type MetricStatus = 'good' | 'warning' | 'poor';

export interface FinancialMetric {
  name: string;
  value: number;
  formatted_value: string;
  category: 'liquidity' | 'profitability' | 'leverage';
  citations: Citation[];
  interpretation?: MetricInterpretation;
}

export interface AIInsight {
  category: 'risk_assessment' | 'liquidity_position' | 'financial_health' | 'recommendations';
  title: string;
  content: string;
  supporting_metrics?: string[];
  citations?: Citation[];
  severity?: 'low' | 'medium' | 'high';
}

export interface AnalysisResult {
  id: string;
  document_id: string;
  analysis_type: AnalysisType;
  quality_score: number;
  metrics: FinancialMetric[];
  insights: AIInsight[];
  created_at: string;
  updated_at: string;
  cached: boolean;
}
```

### Base UI Components

#### 18. **Button** (`/frontend/src/components/ui/Button.tsx`) - 81 lines
**Variants**: primary, secondary, outline, ghost, danger
**Sizes**: sm, md, lg
**Features**: Loading state, icons, disabled state

#### 19. **Card** (`/frontend/src/components/ui/Card.tsx`) - 89 lines
**Components**: Card, CardHeader, CardTitle, CardContent, CardFooter
**Props**: padding, hover effect

#### 20. **Badge** (`/frontend/src/components/ui/Badge.tsx`) - 43 lines
**Variants**: default, success, warning, danger, info
**Sizes**: sm, md, lg

#### 21. **Input** (`/frontend/src/components/ui/Input.tsx`) - 51 lines
**Features**: Label, error state, left/right icons

#### 22. **Spinner** (`/frontend/src/components/ui/Spinner.tsx`) - 52 lines
**Components**: Spinner, LoadingOverlay
**Sizes**: sm, md, lg, xl

## Dependencies

### Required Packages (Already Installed)
```json
{
  "recharts": "^2.12.0",         // Charts and visualizations
  "date-fns": "^3.3.0",          // Date formatting
  "@tanstack/react-query": "^5.17.19",  // Data fetching
  "react-router-dom": "^6.21.3", // Routing
  "clsx": "^2.1.0",              // Conditional classes
  "tailwind-merge": "^2.2.0"     // Tailwind utilities
}
```

### Optional Icons (Consider Adding)
```bash
npm install lucide-react
```

## Integration Guide

### 1. Add Route to Router

```typescript
// In your App.tsx or router configuration
import { AnalysisPage } from './pages/AnalysisPage';

<Route path="/cases/:caseId/documents/:documentId/analysis" element={<AnalysisPage />} />
```

### 2. Link from Document Details

```typescript
// In DocumentDetails component
import { useNavigate } from 'react-router-dom';

const navigate = useNavigate();

<Button
  onClick={() => navigate(`/cases/${caseId}/documents/${documentId}/analysis`)}
>
  View Analysis
</Button>
```

### 3. Backend API Endpoints Required

```
GET    /api/documents/:documentId/analysis/:analysisType
POST   /api/documents/:documentId/analysis/:analysisType
GET    /api/documents/:documentId/analysis/history
GET    /api/documents/:documentId/analysis/:analysisType/export?format=pdf|excel|json
POST   /api/cases/:caseId/semantic-search
GET    /api/cases/:caseId/saved-searches
POST   /api/cases/:caseId/saved-searches
```

## Color Coding System

### Status Colors
- **Good**: `green-600` (#16a34a) - Positive metrics
- **Warning**: `yellow-600` (#ca8a04) - Neutral/moderate metrics
- **Poor**: `red-600` (#dc2626) - Negative metrics
- **Info**: `blue-600` (#2563eb) - Informational

### Insight Categories
- **Risk Assessment**: Red theme
- **Liquidity Position**: Blue theme
- **Financial Health**: Green theme
- **Recommendations**: Yellow theme

## File Structure

```
frontend/src/
├── pages/
│   └── AnalysisPage.tsx                    (246 lines)
├── components/
│   ├── analysis/
│   │   ├── AnalysisTypeSelector.tsx        (58 lines)
│   │   ├── AnalysisResults.tsx             (241 lines)
│   │   ├── AnalysisHistory.tsx             (270 lines)
│   │   ├── QualityScoreCard.tsx            (122 lines)
│   │   ├── MetricsTable.tsx                (259 lines)
│   │   ├── MetricsCharts.tsx               (289 lines)
│   │   ├── MetricCard.tsx                  (124 lines)
│   │   ├── InsightsPanel.tsx               (212 lines)
│   │   ├── SemanticSearch.tsx              (207 lines)
│   │   ├── SearchResults.tsx               (247 lines)
│   │   ├── CitationLink.tsx                (77 lines)
│   │   ├── ExportMenu.tsx                  (263 lines)
│   │   └── index.ts                        (13 lines)
│   └── ui/
│       ├── Button.tsx                       (81 lines)
│       ├── Card.tsx                         (89 lines)
│       ├── Badge.tsx                        (43 lines)
│       ├── Input.tsx                        (51 lines)
│       ├── Spinner.tsx                      (52 lines)
│       └── index.ts                         (6 lines)
├── hooks/
│   ├── useAnalysis.ts                       (229 lines)
│   └── useSemanticSearch.ts                 (86 lines)
├── lib/
│   └── metricInterpretation.ts              (328 lines)
└── types/
    └── analysis.ts                          (102 lines)
```

## Total Statistics

- **Total Files Created**: 22
- **Total Lines of Code**: ~3,469 lines
- **Components**: 17
- **Hooks**: 2
- **Utilities**: 1
- **Type Definitions**: 1
- **UI Components**: 5

## Testing Checklist

### Component Testing
- [ ] AnalysisPage renders with valid route params
- [ ] Analysis type selector changes analysis type
- [ ] Run analysis button triggers API call
- [ ] Quality score card displays correct color
- [ ] Metrics table sorts correctly
- [ ] Charts render with valid data
- [ ] Search returns results
- [ ] Export menu downloads files
- [ ] Citation links open correct pages
- [ ] History shows past analyses

### Integration Testing
- [ ] Navigate from document details to analysis page
- [ ] Run comprehensive analysis end-to-end
- [ ] Export to PDF/Excel/JSON
- [ ] Semantic search with various queries
- [ ] View analysis history and compare
- [ ] Handle errors gracefully
- [ ] Loading states display correctly

### Responsive Testing
- [ ] Mobile layout (< 768px)
- [ ] Tablet layout (768px - 1024px)
- [ ] Desktop layout (> 1024px)
- [ ] Charts resize correctly
- [ ] Tables scroll on mobile

## Performance Considerations

1. **React Query Caching**: Results cached for 5 minutes
2. **Lazy Loading**: Charts render only when visible
3. **Pagination**: Search results paginated (10 per page)
4. **Memoization**: Charts and tables use useMemo
5. **Code Splitting**: Consider lazy loading AnalysisPage

## Future Enhancements

1. **Comparison Mode**: Compare multiple analyses side-by-side
2. **Custom Metrics**: Allow users to define custom ratios
3. **Alerts**: Set thresholds for metric alerts
4. **Benchmarking**: Compare against industry standards
5. **PDF Templates**: Customizable export templates
6. **Real-time Updates**: WebSocket for live analysis updates
7. **Annotations**: Add notes to specific metrics
8. **Sharing**: Share analysis with team members
9. **Scheduling**: Schedule periodic analyses
10. **AI Chat**: Conversational interface for insights

## Support and Maintenance

For issues or questions about the Analysis Viewer system:
1. Check type definitions in `analysis.ts`
2. Review interpretation logic in `metricInterpretation.ts`
3. Test with sample data
4. Verify API endpoints are responding
5. Check browser console for errors

## License

Part of the Investigation Intelligence Platform - Phase 5 Frontend Development
