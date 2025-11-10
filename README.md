# Investigation Intelligence Platform

Multi-document analysis system for financial investigations supporting 2,000-10,000 pages per case.

## 🎯 Project Status: **PROTOTYPE IN DEVELOPMENT**

### ✅ Completed Components

**Infrastructure:**
- [x] Project structure
- [x] Docker Compose (Postgres, Qdrant, Elasticsearch, Redis, Neo4j)
- [x] Database schemas
- [x] Configuration system
- [x] Environment setup

**Architecture:**
- [x] Multi-agent orchestration integration
- [x] System architecture design
- [x] LM Studio endpoint configuration (192.168.200.226:1234)
- [x] Micro-agent prompt templates

### 🚧 In Progress

- [ ] PDF extraction pipeline (PyMaster)
- [ ] Embeddings system (EmbedPro)
- [ ] Database connection layer (DBMaster)
- [ ] LM Studio client (LLMExpert)
- [ ] Financial calculators (DataWiz)
- [ ] FastAPI backend
- [ ] React frontend
- [ ] Analysis orchestration
- [ ] Report generators

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────┐
│    React Frontend (Port 5173)           │
│    - Case Management                    │
│    - Document Upload (Progressive)      │
│    - Analysis Progress                  │
│    - Reports Viewer                     │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│    FastAPI Backend (Port 8000)          │
│    - REST API                           │
│    - Document Processing                │
│    - Analysis Engine                    │
│    - Micro-Agent Orchestration          │
└───────────────┬─────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
┌───────▼──────┐  ┌──────▼────────┐
│  Databases   │  │  LM Studio    │
│              │  │  192.168...   │
│ • Postgres   │  │  :1234        │
│ • Qdrant     │  └───────────────┘
│ • Elastic    │
│ • Redis      │
│ • Neo4j      │
└──────────────┘
```

### Key Features

**Document Processing:**
- PDF extraction with pdfplumber
- Smart chunking (750 chars, 120 overlap)
- Page-level citation tracking
- Progressive upload support

**Analysis Engine:**
- 90% deterministic Python calculations
- 10% micro-LLM calls (max 50 input, 10 output tokens)
- 50+ financial metrics
- Parallel micro-agent execution

**Storage Strategy:**
- **PostgreSQL**: Cases, documents, metrics, citations
- **Qdrant**: Vector embeddings (E5 large, 1024 dim)
- **Elasticsearch**: Full-text search
- **Redis**: Caching & state management
- **Neo4j**: Entity relationships (future)

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)
- LM Studio running at 192.168.200.226:1234
```

### 2. Start Databases

```bash
cd /Users/artur/agents20/projektagenci01

# Start all database services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f
```

**Services will be available at:**
- PostgreSQL: `localhost:5432`
- Qdrant: `localhost:6333`
- Elasticsearch: `localhost:9200`
- Redis: `localhost:6379`
- Neo4j: `localhost:7474` (UI), `localhost:7687` (Bolt)

### 3. Setup Backend (When ready)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example .env

# Run backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Setup Frontend (When ready)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## 📁 Project Structure

```
projektagenci01/
├── README.md
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── requirements.txt
│   ├── src/
│   │   ├── api/                  # FastAPI routes
│   │   ├── core/                 # Business logic
│   │   │   ├── extractors/       # PDF processing
│   │   │   ├── calculators/      # Financial metrics
│   │   │   └── micro_agents/     # LLM micro-agents
│   │   ├── storage/              # Database connections
│   │   ├── orchestration/        # Analysis workflow
│   │   └── config/               # Configuration
│   └── tests/
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── pages/                # Page components
│   │   ├── hooks/                # Custom hooks
│   │   └── api/                  # API client
│
├── data/                         # Docker volumes
│   ├── uploads/                  # Uploaded documents
│   ├── postgres/
│   ├── qdrant/
│   ├── elastic/
│   ├── redis/
│   └── neo4j/
│
└── scripts/
    ├── init_postgres.sql         # Database schema
    └── setup.sh                  # Setup script
```

---

## 🔧 Configuration

### LM Studio Integration

Your local LLM server configuration in `.env`:

```bash
LLM_ENDPOINT=http://192.168.200.226:1234/v1
LLM_DEFAULT_MODEL=gemma
LLM_TIMEOUT=30
```

**Supported Models:**
- OSS (40k token window)
- Gemma (40k token window)

### Micro-Agent Prompts

Configured in `backend/src/config/settings.py`:

```python
MICRO_AGENT_PROMPTS = {
    "debt_level": {
        "template": "Debt/Equity={value:.2f}. Classification:",
        "expected_outputs": ["low", "moderate", "high", "critical"],
        "max_tokens": 1
    },
    # ... more micro-agents
}
```

---

## 📊 Database Schemas

### PostgreSQL Tables

- **cases**: Investigation cases
- **documents**: Uploaded documents
- **entities**: Extracted entities
- **financial_metrics**: Calculated metrics
- **analysis_results**: Analysis outputs
- **citations**: Source citations
- **processing_status**: Progress tracking
- **micro_agent_cache**: LLM response cache

See `scripts/init_postgres.sql` for complete schema.

---

## 🧪 Development Workflow

### Using the Multi-Agent System

The project integrates with the 6-agent orchestration system:

```bash
# Run the agent-coordinated build
python3 build_with_agents.py
```

This activates:
- **Artur**: Architecture & coordination
- **PyMaster**: Backend development
- **DataWiz**: Financial analysis
- **LLMExpert**: LM Studio integration
- **EmbedPro**: Embeddings pipeline
- **DBMaster**: Database layer

---

## 📖 API Documentation

### REST Endpoints (When implemented)

```
POST   /api/v1/cases              Create new case
GET    /api/v1/cases              List all cases
GET    /api/v1/cases/{id}         Get case details

POST   /api/v1/cases/{id}/documents    Upload document
GET    /api/v1/cases/{id}/documents    List documents

POST   /api/v1/analysis/{case_id}      Start analysis
GET    /api/v1/analysis/{case_id}      Get analysis results

GET    /api/v1/reports/{case_id}/executive    Executive summary
GET    /api/v1/reports/{case_id}/deep-dive    Deep dive report
```

---

## 🎯 Roadmap

### Phase 1: Foundation (Current)
- [x] Infrastructure setup
- [x] Database schemas
- [x] Configuration
- [ ] Core backend structure
- [ ] Basic document processing

### Phase 2: Document Pipeline
- [ ] PDF extraction
- [ ] Embeddings generation
- [ ] Database storage
- [ ] Progress tracking

### Phase 3: Analysis Engine
- [ ] Financial calculators
- [ ] Micro-agent system
- [ ] LM Studio integration
- [ ] Metrics calculation

### Phase 4: Reports
- [ ] Executive summary generator
- [ ] Deep dive with citations
- [ ] Export functionality

### Phase 5: Frontend
- [ ] React dashboard
- [ ] Document upload UI
- [ ] Analysis viewer
- [ ] Report display

### Phase 6: Enhancement
- [ ] Legal document support
- [ ] Entity extraction (NER)
- [ ] Neo4j relationships
- [ ] Advanced analytics

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if databases are running
docker-compose ps

# Restart services
docker-compose restart

# View logs
docker-compose logs postgres
docker-compose logs qdrant
```

### LM Studio Connection

```bash
# Test LM Studio endpoint
curl http://192.168.200.226:1234/v1/models

# Check if models are loaded
curl http://192.168.200.226:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma","messages":[{"role":"user","content":"test"}],"max_tokens":5}'
```

---

## 📝 Notes

- **Prototype Focus**: Financial documents first, legal documents later
- **Progressive Upload**: Documents can be added to existing cases
- **Citation Tracking**: Every metric links back to source page
- **Deterministic**: 90% pure Python, 10% micro-LLM calls
- **Scalable**: Designed for 2,000-10,000 pages per case

---

## 👥 Agent Team Contributions

Built with multi-agent orchestration:
- Artur: Architecture design
- PyMaster: Backend implementation
- DataWiz: Financial analysis
- LLMExpert: LM Studio integration
- EmbedPro: Embeddings pipeline
- DBMaster: Database layer

---

## 📧 Support

For issues or questions, refer to the architecture documentation in `ARCHITECTURE.md`.

---

**Status**: Prototype in active development
**Next**: Implementing PDF extraction pipeline and database connection layer
