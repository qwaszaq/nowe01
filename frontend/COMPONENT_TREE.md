# Analysis Viewer Component Tree

## Component Hierarchy

```
AnalysisPage (Main Route: /cases/:caseId/documents/:documentId/analysis)
│
├── Header Section
│   ├── Back Button (navigate to document details)
│   ├── Page Title
│   └── View History Button
│
├── AnalysisTypeSelector
│   ├── Comprehensive Tab
│   ├── Liquidity Tab
│   ├── Profitability Tab
│   ├── Leverage Tab
│   └── Quick Tab
│
├── Run Analysis Section
│   ├── Status Message (cached/new)
│   ├── Run Analysis Button
│   ├── Refresh Button (if cached)
│   ├── Progress Bar (when running)
│   └── Error Message (if failed)
│
├── AnalysisHistory (conditional: if showHistory)
│   └── History Items
│       ├── Analysis Type Badge
│       ├── Quality Score Badge
│       ├── Timestamp
│       ├── Metrics Count
│       ├── View Button
│       └── Compare Button
│
├── AnalysisResults (if data available)
│   │
│   ├── Results Header
│   │   ├── Title
│   │   ├── Timestamp Info
│   │   └── ExportMenu
│   │       ├── Export as PDF
│   │       ├── Export as Excel
│   │       ├── Export as JSON
│   │       └── Email Report
│   │
│   ├── Main Grid (12-column)
│   │   │
│   │   ├── Left Column (8 cols)
│   │   │   │
│   │   │   ├── QualityScoreCard
│   │   │   │   ├── Circular Progress Chart (Recharts PieChart)
│   │   │   │   ├── Score Number (0-100)
│   │   │   │   ├── Quality Label (Excellent/Good/Fair/Poor)
│   │   │   │   ├── Description Text
│   │   │   │   ├── Legend (score ranges)
│   │   │   │   └── Explanation Footer
│   │   │   │
│   │   │   └── Metrics Display Section
│   │   │       ├── Header with View Mode Toggle
│   │   │       │   ├── Grid View Button
│   │   │       │   ├── Table View Button
│   │   │       │   └── Charts View Button
│   │   │       │
│   │   │       ├── MetricCardGrid (if grid mode)
│   │   │       │   └── MetricCard (for each metric)
│   │   │       │       ├── Metric Name
│   │   │       │       ├── Value Display (large)
│   │   │       │       ├── Status Badge (Good/Warning/Poor)
│   │   │       │       ├── Interpretation Text
│   │   │       │       ├── CitationList
│   │   │       │       └── Expandable Details
│   │   │       │           ├── Category
│   │   │       │           ├── Raw Value
│   │   │       │           └── Source Document
│   │   │       │
│   │   │       ├── MetricsTable (if table mode)
│   │   │       │   └── Category Sections (Liquidity/Profitability/Leverage)
│   │   │       │       ├── Category Header
│   │   │       │       └── Table
│   │   │       │           ├── Header Row
│   │   │       │           │   ├── Ratio Name (sortable)
│   │   │       │           │   ├── Value (sortable)
│   │   │       │           │   ├── Status (sortable)
│   │   │       │           │   └── Citation
│   │   │       │           └── Metric Rows
│   │   │       │               ├── Main Row
│   │   │       │               │   ├── Expand Icon
│   │   │       │               │   ├── Metric Name
│   │   │       │               │   ├── Formatted Value
│   │   │       │               │   ├── Status Badge
│   │   │       │               │   └── CitationList
│   │   │       │               └── Expanded Row (if expanded)
│   │   │       │                   ├── Interpretation
│   │   │       │                   ├── Category
│   │   │       │                   └── Raw Value
│   │   │       │
│   │   │       └── MetricsCharts (if charts mode)
│   │   │           ├── Chart Type Selector
│   │   │           │   ├── Bar Chart Button
│   │   │           │   ├── Line Chart Button
│   │   │           │   └── Radar Chart Button
│   │   │           │
│   │   │           └── Charts (Recharts)
│   │   │               ├── Bar Charts (if bar mode)
│   │   │               │   ├── Liquidity Ratios Chart
│   │   │               │   ├── Profitability Ratios Chart
│   │   │               │   └── Leverage Ratios Chart
│   │   │               │
│   │   │               ├── Line Charts (if line mode)
│   │   │               │   ├── Liquidity Trends
│   │   │               │   ├── Profitability Trends
│   │   │               │   └── Leverage Trends
│   │   │               │
│   │   │               └── Radar Chart (if radar mode)
│   │   │                   └── Overall Metrics Overview
│   │   │
│   │   └── Right Column (4 cols)
│   │       │
│   │       └── InsightsPanel
│   │           ├── Panel Header
│   │           └── Insight Cards
│   │               ├── Risk Assessment Insight
│   │               │   ├── Category Icon (Red)
│   │               │   ├── Title
│   │               │   ├── Severity Badge
│   │               │   ├── Content
│   │               │   ├── Supporting Metrics
│   │               │   └── CitationList
│   │               │
│   │               ├── Liquidity Position Insight
│   │               │   ├── Category Icon (Blue)
│   │               │   └── [same structure]
│   │               │
│   │               ├── Financial Health Insight
│   │               │   ├── Category Icon (Green)
│   │               │   └── [same structure]
│   │               │
│   │               └── Recommendations Insight
│   │                   ├── Category Icon (Yellow)
│   │                   └── [same structure]
│   │
│   └── Summary Statistics Row
│       ├── Total Metrics Card
│       │   ├── Count
│       │   └── Icon
│       ├── AI Insights Card
│       │   ├── Count
│       │   └── Icon
│       └── Analysis Type Card
│           ├── Type Name
│           └── Icon
│
└── SemanticSearch (full width)
    ├── Search Header
    ├── Search Input
    │   ├── Search Icon
    │   ├── Input Field
    │   └── Search Button
    │
    ├── Example Queries (chips)
    │   ├── "What is the revenue growth trend?"
    │   ├── "How has debt changed over time?"
    │   ├── "What are the main expenses?"
    │   └── [other examples]
    │
    ├── Loading State (if pending)
    │   ├── Spinner
    │   └── Message
    │
    ├── Error State (if error)
    │   ├── Error Icon
    │   └── Error Message
    │
    └── SearchResults (if results)
        ├── Results Header
        │   ├── Count Display
        │   └── Sort Dropdown
        │       ├── Sort by Relevance
        │       └── Sort by Page
        │
        ├── Result Cards
        │   └── Result Card (for each result)
        │       ├── Score Bar
        │       ├── Document Info
        │       │   ├── Document Name
        │       │   └── Page Number
        │       ├── Text Excerpt (with highlighting)
        │       ├── Metadata Tags
        │       └── View in Context Button
        │
        └── Pagination
            ├── Previous Button
            ├── Page Numbers
            └── Next Button
```

## Data Flow Diagram

```
User Actions → Component Events → React Query Hooks → API Calls → Backend

1. Select Analysis Type
   AnalysisTypeSelector → setAnalysisType() → useAnalysis() hook updates

2. Run Analysis
   Button Click → useRunAnalysis().mutateAsync() → POST /api/documents/:id/analysis/:type
   → Response → Cache Update → AnalysisResults re-render

3. View Metrics
   AnalysisResults → receives data → renders based on viewMode
   → Grid: MetricCardGrid
   → Table: MetricsTable
   → Charts: MetricsCharts

4. Search Documents
   SemanticSearch input → useSemanticSearch().mutateAsync() → POST /api/cases/:id/semantic-search
   → SearchResults → Display with pagination

5. Export Data
   ExportMenu → useExportAnalysis().mutateAsync() → GET /api/documents/:id/analysis/:type/export
   → Blob response → Browser download

6. View History
   Toggle history → useAnalysisHistory() → GET /api/documents/:id/analysis/history
   → AnalysisHistory → List of past analyses

7. Citation Click
   CitationLink → onCitationClick callback → window.open() or navigate to document viewer
```

## State Management

```
Component State (useState):
├── AnalysisPage
│   ├── analysisType: AnalysisType
│   └── showHistory: boolean
│
├── AnalysisResults
│   └── metricsViewMode: 'grid' | 'table' | 'charts'
│
├── MetricsTable
│   ├── sortField: 'name' | 'value' | 'status'
│   ├── sortDirection: 'asc' | 'desc'
│   └── expandedRows: Set<string>
│
├── MetricsCharts
│   └── chartType: 'bar' | 'line' | 'radar'
│
├── MetricCard
│   └── expanded: boolean
│
├── SearchResults
│   ├── currentPage: number
│   └── sortBy: 'relevance' | 'page'
│
├── SemanticSearch
│   └── query: string
│
├── ExportMenu
│   └── isOpen: boolean
│
└── AnalysisHistory
    └── selectedForCompare: AnalysisResult | null

React Query State (managed by hooks):
├── useAnalysis
│   ├── data: AnalysisResult
│   ├── isLoading: boolean
│   └── isError: boolean
│
├── useRunAnalysis
│   ├── isPending: boolean
│   └── isError: boolean
│
├── useSemanticSearch
│   ├── data: SearchResult[]
│   ├── isPending: boolean
│   └── isError: boolean
│
└── useAnalysisHistory
    ├── data: AnalysisResult[]
    └── isLoading: boolean
```

## Component Dependencies Graph

```
AnalysisPage
├── depends on: react-router-dom, date-fns
├── uses hooks: useAnalysis, useRunAnalysis
└── imports:
    ├── AnalysisTypeSelector
    ├── AnalysisResults
    ├── SemanticSearch
    ├── AnalysisHistory
    ├── Button
    └── LoadingOverlay

AnalysisResults
├── depends on: none
└── imports:
    ├── QualityScoreCard
    ├── MetricsTable
    ├── MetricsCharts
    ├── MetricCardGrid
    ├── InsightsPanel
    └── ExportMenu

MetricsTable
├── depends on: none
└── imports:
    ├── CitationList
    ├── Card components
    └── metricInterpretation utils

MetricsCharts
├── depends on: recharts
└── imports:
    ├── Card components
    └── metricInterpretation utils

InsightsPanel
├── depends on: none
└── imports:
    ├── CitationList
    ├── Card components
    └── Badge

SemanticSearch
├── depends on: none
├── uses hooks: useSemanticSearch
└── imports:
    ├── SearchResults
    ├── Input
    ├── Button
    └── Card components

All components use:
├── clsx (for conditional classes)
└── TypeScript types from types/analysis.ts
```

## Reusable Components Used Across System

```
Card Components (used by all)
├── Card
├── CardHeader
├── CardTitle
├── CardContent
└── CardFooter

Button (used by 8+ components)
├── AnalysisPage
├── SemanticSearch
├── ExportMenu
├── AnalysisHistory
└── [others]

Badge (used by 6+ components)
├── QualityScoreCard
├── InsightsPanel
├── AnalysisHistory
└── [others]

CitationLink/CitationList (used by 4 components)
├── MetricCard
├── MetricsTable
├── InsightsPanel
└── SearchResults

LoadingOverlay (used by 3 components)
├── AnalysisPage
├── AnalysisHistory
└── [others]
```

## File Size Distribution

```
Large Components (200+ lines):
├── MetricsCharts.tsx        289 lines  [Complex chart logic]
├── AnalysisHistory.tsx      270 lines  [Timeline & comparison]
├── ExportMenu.tsx           263 lines  [Multiple export formats]
├── MetricsTable.tsx         259 lines  [Sortable table logic]
├── SearchResults.tsx        247 lines  [Pagination & highlighting]
├── AnalysisPage.tsx         246 lines  [Main orchestrator]
├── AnalysisResults.tsx      241 lines  [View mode switching]
└── InsightsPanel.tsx        212 lines  [Multiple insight types]

Medium Components (100-200 lines):
├── MetricCard.tsx           124 lines
├── QualityScoreCard.tsx     122 lines
└── [others]

Small Components (< 100 lines):
├── Button.tsx                81 lines
├── Card.tsx                  89 lines
├── CitationLink.tsx          77 lines
├── AnalysisTypeSelector.tsx  58 lines
└── [others]

Utility Files:
├── metricInterpretation.ts  328 lines  [19 ratio rules]
├── useAnalysis.ts           229 lines  [4 hooks]
└── analysis.ts              102 lines  [Type definitions]
```

This tree structure shows how all 24 files work together to create a comprehensive financial analysis viewer system.
