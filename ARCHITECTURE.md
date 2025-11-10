# Investigation Intelligence Platform - Architecture

## System Overview

**Purpose**: Multi-document investigation support system for analyzing 2,000-10,000 pages of financial, legal, and operational documents.

**Core Principle**: 90% deterministic Python + 10% micro-LLM calls

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    React Dashboard (Frontend)                    │
│  Case Management | Upload | Progress | Analysis | Reports       │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Case Mgmt   │  │  Document    │  │  Analysis    │         │
│  │  Service     │  │  Processor   │  │  Engine      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────┬────────────────┬────────────────┬───────────────────┘
           │                │                │
    ┌──────▼────────┐  ┌───▼────────┐  ┌───▼────────┐
    │  PostgreSQL   │  │  Document  │  │  Analysis  │
    │  (Cases,      │  │  Pipeline  │  │  Pipeline  │
    │   Metadata)   │  │            │  │            │
    └───────────────┘  └─────┬──────┘  └─────┬──────┘
                             │                │
              ┌──────────────┼────────────────┼──────────────┐
              │              │                │              │
         ┌────▼────┐   ┌────▼────┐   ┌──────▼─────┐   ┌───▼────┐
         │ Qdrant  │   │ Elastic │   │ LM Studio  │   │ Redis  │
         │(Vectors)│   │(Search) │   │192.168...  │   │(Cache) │
         └─────────┘   └─────────┘   └────────────┘   └────────┘
```

---

## Component Architecture

### 1. Frontend Layer (React)

**Technology Stack:**
- React 18+ with TypeScript
- Vite for build system
- TailwindCSS for styling
- React Query for data fetching
- Zustand for state management
- React Router for navigation

**Key Components:**
```
frontend/
├── src/
│   ├── components/
│   │   ├── CaseManager/        # Case creation & listing
│   │   ├── DocumentUpload/     # Drag & drop, progressive upload
│   │   ├── AnalysisViewer/     # Real-time progress
│   │   ├── ExecutiveSummary/   # High-level findings
│   │   └── DeepDiveReport/     # Detailed analysis with citations
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── CaseDetails.tsx
│   │   └── Reports.tsx
│   ├── hooks/
│   │   ├── useCases.ts
│   │   ├── useDocuments.ts
│   │   └── useAnalysis.ts
│   └── api/
│       └── client.ts           # API integration
```

### 2. Backend Layer (FastAPI)

**Core Services:**

#### A. Case Management Service
```python
Responsibilities:
- Create new investigation cases
- Manage case metadata
- Track case status
- Associate documents with cases
- Handle case lifecycle

Database: PostgreSQL
```

#### B. Document Processing Pipeline
```python
Stages:
1. Upload → Validate → Store
2. Extract → PDF/DOCX parsing
3. Chunk → Smart chunking (750 chars, 120 overlap)
4. Embed → E5 large embeddings
5. Index → Qdrant + Elasticsearch
6. Metadata → PostgreSQL

Handles:
- PDFs (financial reports, contracts)
- Progressive uploads (add to existing case)
- Large files (2,000-10,000 pages)
- Progress tracking (Redis)
```

#### C. Analysis Engine
```python
Flow:
1. Data Extraction (deterministic)
   - Tables from PDFs
   - Text sections
   - Metadata

2. Calculation Layer (pure Python)
   - Financial ratios (50+ metrics)
   - Trend analysis
   - Statistical computations

3. Micro-Agent Layer (LLM calls)
   - Classification (max 10 tokens)
   - Risk assessment (max 10 tokens)
   - Sentiment (max 10 tokens)
   - Run 10+ in parallel

4. Synthesis Layer
   - Cross-document analysis
   - Timeline construction
   - Entity relationships

5. Report Generation
   - Executive Summary (5-10 pages)
   - Deep Dive (50-200 pages with citations)
```

### 3. Storage Layer

#### PostgreSQL - Structured Data
```sql
Tables:
- cases (id, name, created_at, status, ...)
- documents (id, case_id, filename, pages, status, ...)
- entities (id, type, name, ...)
- metrics (id, document_id, metric_name, value, page_num)
- analysis_results (id, case_id, summary, deep_dive, ...)
- citations (id, metric_id, page_num, text_excerpt)
```

#### Qdrant - Semantic Search
```python
Collection: financial_docs
Vector dimension: 1024 (E5 large)
Metadata per vector:
- case_id
- document_id
- page_num
- chunk_id
- document_type (financial/legal/operational)
```

#### Elasticsearch - Exact Search
```python
Index: investigation_docs
Fields:
- full_text (analyzed)
- case_id
- document_id
- page_num
- document_type
- date_extracted
```

#### Redis - State & Cache
```python
Keys:
- processing_status:{case_id}
- document_progress:{doc_id}
- analysis_state:{case_id}
- embeddings_cache:{chunk_hash}
- llm_response_cache:{prompt_hash}
```

#### Neo4j - Relationships (Future)
```cypher
Nodes:
- Company
- Person
- Document
- Transaction
- Date

Relationships:
- OWNS
- MENTIONED_IN
- TRANSACTED_WITH
- SIGNED_BY
```

### 4. Integration Layer

#### LM Studio Integration
```python
Endpoint: http://192.168.200.226:1234/v1/chat/completions
Models: OSS, Gemma (40k token window)

Usage Strategy:
- Micro-prompts only (max 50 tokens input)
- Parallel execution (10+ simultaneous)
- Timeout: 30s per call
- Retry: 3 attempts
- Fallback: Rule-based decisions

Micro-Agent Examples:
{
  "debt_assessment": {
    "prompt": "Debt/Equity={ratio}. Risk:",
    "expected": ["low", "moderate", "high"],
    "tokens": 1
  },
  "trend_direction": {
    "prompt": "Revenue YoY={change}%. Trend:",
    "expected": ["growth", "stable", "decline"],
    "tokens": 1
  }
}
```

#### Embeddings Pipeline
```python
Model: intfloat/multilingual-e5-large
Dimension: 1024
Batch size: 32
Processing: GPU-accelerated

Flow:
1. Chunk text (750 chars)
2. Batch chunks (32 per batch)
3. Generate embeddings
4. Store in Qdrant
5. Cache in Redis
```

---

## Data Flow

### Document Upload & Processing

```
User uploads PDF
  ↓
FastAPI receives file
  ↓
Save to disk (/data/uploads/{case_id}/{doc_id}.pdf)
  ↓
Create document record (PostgreSQL)
  ↓
Background task starts
  ↓
  ┌─ Extract pages (pdfplumber)
  ├─ Extract tables
  ├─ Create chunks (750/120)
  ├─ Generate embeddings (E5)
  ├─ Store in Qdrant
  ├─ Index in Elasticsearch
  └─ Update progress (Redis)
  ↓
Document ready for analysis
```

### Analysis Execution

```
User requests analysis for case
  ↓
Fetch all documents in case
  ↓
Deterministic Phase (90%):
  ├─ Extract financial data from tables
  ├─ Calculate 50+ metrics
  ├─ Detect anomalies
  └─ Build timeline
  ↓
Micro-Agent Phase (10%):
  ├─ Run 10+ micro-agents in parallel
  ├─ Each: max 50 token input, 10 token output
  ├─ Classify risks, trends, sentiments
  └─ Aggregate results
  ↓
Synthesis Phase:
  ├─ Cross-document patterns
  ├─ Relationship mapping
  └─ Citation tracking
  ↓
Report Generation:
  ├─ Executive Summary (LLM-assisted synthesis)
  └─ Deep Dive (deterministic + citations)
  ↓
Store results (PostgreSQL)
  ↓
Notify user (WebSocket/polling)
```

---

## Scalability Considerations

### Document Processing
- **Async processing**: Background tasks with Celery/RQ
- **Parallel extraction**: Process multiple docs simultaneously
- **Chunked uploads**: Stream large files
- **Progress tracking**: Real-time updates via Redis

### Analysis
- **Batch processing**: Group similar operations
- **Parallel micro-agents**: 10+ concurrent LLM calls
- **Caching**: Redis for repeated calculations
- **Incremental**: Add documents without reprocessing entire case

### Storage
- **Qdrant**: Horizontal scaling for vector search
- **Elasticsearch**: Distributed for text search
- **PostgreSQL**: Connection pooling, read replicas
- **Redis**: Cluster mode for high availability

---

## Security & Privacy

- **Document isolation**: Each case isolated in database
- **Access control**: Case-level permissions (future)
- **Data retention**: Configurable cleanup policies
- **Audit logging**: All operations tracked
- **Local deployment**: All data stays on your infrastructure

---

## Prototype Scope

**Included:**
✅ React dashboard (case mgmt, upload, progress, reports)
✅ Document upload (PDF, progressive)
✅ PDF extraction & chunking
✅ Embeddings with E5 large
✅ Storage in all databases
✅ Financial metrics calculation (top 20 metrics)
✅ 5 micro-agents
✅ Executive summary generation
✅ Deep dive with citations
✅ LM Studio integration (192.168.200.226)

**Deferred (Post-Prototype):**
⏳ Legal document parsing
⏳ Entity extraction (NER)
⏳ Neo4j relationships
⏳ Advanced anomaly detection
⏳ Multi-user support
⏳ Export to PDF/DOCX

---

## Development Phases

### Phase 1: Foundation (Week 1)
- [ ] Project structure
- [ ] Docker Compose
- [ ] Database schemas
- [ ] Basic FastAPI app
- [ ] React scaffold

### Phase 2: Document Pipeline (Week 2)
- [ ] PDF extraction
- [ ] Chunking logic
- [ ] Embeddings integration
- [ ] Storage layer
- [ ] Upload UI

### Phase 3: Analysis Engine (Week 3)
- [ ] Financial calculations
- [ ] Micro-agents
- [ ] LM Studio integration
- [ ] Analysis orchestration
- [ ] Progress tracking

### Phase 4: Reports (Week 4)
- [ ] Executive summary
- [ ] Deep dive generator
- [ ] Citation tracking
- [ ] Report UI
- [ ] Export functionality

---

## Technology Stack Summary

**Frontend:**
- React 18 + TypeScript + Vite
- TailwindCSS
- React Query + Zustand

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy (ORM)
- Pydantic (validation)
- Celery (async tasks)

**Databases:**
- PostgreSQL 15
- Qdrant (latest)
- Elasticsearch 8.11
- Redis 7

**AI/ML:**
- LM Studio (192.168.200.226:1234)
- E5 large embeddings
- Sentence Transformers

**Infrastructure:**
- Docker Compose
- Nginx (reverse proxy)
- Local deployment

---

**Architecture designed by: Artur (Lead Architect)**
**Status: Ready for implementation**
