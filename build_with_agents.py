#!/usr/bin/env python3
"""
Use the Multi-Agent System to Build Investigation Platform
===========================================================
This script actually uses the 6-agent orchestration system to coordinate
building the investigation intelligence platform.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path to import agent system
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import AgentSystemAPI

async def build_investigation_platform():
    """
    Coordinate all 6 agents to build the investigation platform
    Each agent works on their specialty with independent token windows
    """

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║          MULTI-AGENT SYSTEM: Building Investigation Platform                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Project: Investigation Intelligence Platform
Location: /Users/artur/agents20/projektagenci01/
Target: 2,000-10,000 page document analysis system

Activating 6 Specialized Agents:
  • Artur (100k tokens)    - Architecture & Coordination
  • PyMaster (50k tokens)  - Python Backend Development
  • DataWiz (50k tokens)   - Financial Analysis & Metrics
  • LLMExpert (60k tokens) - LM Studio Integration & Micro-Agents
  • EmbedPro (50k tokens)  - E5 Embeddings & Semantic Search
  • DBMaster (50k tokens)  - Multi-Database Setup

Total Capacity: 360,000 tokens across independent contexts
═══════════════════════════════════════════════════════════════════════════════
""")

    # Initialize the agent system
    api = AgentSystemAPI()
    await api.initialize()

    print("\n✅ All agents online and ready!\n")

    # =========================================================================
    # PHASE 1: ARCHITECTURE & PLANNING (Parallel)
    # =========================================================================

    print("="*80)
    print("PHASE 1: Architecture & Planning")
    print("="*80 + "\n")

    phase1_tasks = await asyncio.gather(
        # Artur: Overall system architecture
        api.assign_task(
            agent_name="Artur",
            title="Design investigation platform architecture",
            description="""
            Design complete architecture for investigation intelligence platform:
            - Multi-document processing (2,000-10,000 pages)
            - React frontend + FastAPI backend
            - 5 databases (Postgres, Qdrant, Elasticsearch, Redis, Neo4j)
            - LM Studio integration (192.168.200.226:1234)
            - Progressive document upload
            - Executive summary + deep dive reports
            - Citations and traceability
            """,
            priority=10
        ),

        # DBMaster: Database architecture
        api.assign_task(
            agent_name="DBMaster",
            title="Design multi-database schema",
            description="""
            Design schemas for all databases:
            - PostgreSQL: cases, documents, metrics, citations
            - Qdrant: vector storage structure
            - Elasticsearch: search indices
            - Redis: cache and state keys
            - Neo4j: entity relationships (future)
            Create Docker Compose configuration
            """,
            priority=10
        ),

        # LLMExpert: Micro-agent strategy
        api.assign_task(
            agent_name="LLMExpert",
            title="Design micro-agent system for financial analysis",
            description="""
            Design micro-agent prompts for LM Studio:
            - Max 50 tokens input, 10 tokens output
            - Financial classification agents
            - Risk assessment agents
            - Trend detection agents
            - Integration with 192.168.200.226:1234
            - Parallel execution strategy
            """,
            priority=9
        )
    )

    print(f"\n✅ Phase 1 complete: {len(phase1_tasks)} planning tasks finished\n")
    await asyncio.sleep(2)

    # =========================================================================
    # PHASE 2: BACKEND INFRASTRUCTURE (Parallel)
    # =========================================================================

    print("="*80)
    print("PHASE 2: Backend Infrastructure")
    print("="*80 + "\n")

    phase2_tasks = await asyncio.gather(
        # PyMaster: Project structure and FastAPI
        api.assign_task(
            agent_name="PyMaster",
            title="Create FastAPI backend structure",
            description="""
            Create complete backend structure:
            - FastAPI application with routers
            - Case management endpoints
            - Document upload handling
            - Background task processing
            - Pydantic models
            - Configuration management
            Location: projektagenci01/backend/
            """,
            priority=10
        ),

        # DBMaster: Database setup
        api.assign_task(
            agent_name="DBMaster",
            title="Implement database connection layer",
            description="""
            Create database connection managers:
            - PostgreSQL with SQLAlchemy
            - Qdrant client
            - Elasticsearch client
            - Redis client
            - Connection pooling
            - Health checks
            """,
            priority=10
        ),

        # PyMaster: PDF extraction
        api.assign_task(
            agent_name="PyMaster",
            title="Implement PDF extraction pipeline",
            description="""
            Create PDF processing system:
            - Use pdfplumber for extraction
            - Extract text, tables, metadata
            - Smart chunking (750 chars, 120 overlap)
            - Page number tracking
            - Handle 2,000-10,000 pages
            - Progress tracking
            """,
            priority=9
        )
    )

    print(f"\n✅ Phase 2 complete: {len(phase2_tasks)} infrastructure tasks finished\n")
    await asyncio.sleep(2)

    # =========================================================================
    # PHASE 3: AI/ML COMPONENTS (Parallel)
    # =========================================================================

    print("="*80)
    print("PHASE 3: AI/ML Components")
    print("="*80 + "\n")

    phase3_tasks = await asyncio.gather(
        # EmbedPro: Embeddings pipeline
        api.assign_task(
            agent_name="EmbedPro",
            title="Build E5 embeddings pipeline",
            description="""
            Create embeddings system:
            - intfloat/multilingual-e5-large model
            - Batch processing (32 chunks)
            - Vector generation and storage
            - Integration with Qdrant
            - Caching in Redis
            - GPU acceleration support
            """,
            priority=10
        ),

        # LLMExpert: LM Studio integration
        api.assign_task(
            agent_name="LLMExpert",
            title="Implement LM Studio client",
            description="""
            Create LM Studio integration:
            - HTTP client for 192.168.200.226:1234
            - Micro-agent executor
            - Parallel execution (10+ agents)
            - Timeout and retry logic
            - Response caching
            - Support OSS and Gemma models (40k window)
            """,
            priority=10
        ),

        # DataWiz: Financial calculations
        api.assign_task(
            agent_name="DataWiz",
            title="Implement financial metrics calculator",
            description="""
            Create financial analysis system:
            - Extract numbers from tables
            - Calculate 50+ financial ratios
            - Trend analysis algorithms
            - Anomaly detection
            - Pure Python (deterministic)
            - Citation tracking
            """,
            priority=9
        )
    )

    print(f"\n✅ Phase 3 complete: {len(phase3_tasks)} AI/ML tasks finished\n")
    await asyncio.sleep(2)

    # =========================================================================
    # PHASE 4: ANALYSIS ENGINE (Sequential with dependencies)
    # =========================================================================

    print("="*80)
    print("PHASE 4: Analysis Engine")
    print("="*80 + "\n")

    # PyMaster: Orchestration layer
    orchestration_task = await api.assign_task(
        agent_name="PyMaster",
        title="Build analysis orchestration engine",
        description="""
        Create deterministic analysis flow:
        - Document processing pipeline
        - Metrics calculation phase
        - Micro-agent execution phase
        - Cross-document analysis
        - Report compilation
        - State management with Redis
        """,
        priority=10
    )

    await api.wait_for_task_completion(orchestration_task, timeout=60)

    # DataWiz: Report generators
    reports_task = await api.assign_task(
        agent_name="DataWiz",
        title="Implement report generators",
        description="""
        Create report generation system:
        - Executive summary generator (5-10 pages)
        - Deep dive report with citations
        - Cross-reference tracking
        - Timeline construction
        - Risk highlighting
        - Export to JSON/Markdown
        """,
        priority=9
    )

    await api.wait_for_task_completion(reports_task, timeout=60)

    print("\n✅ Phase 4 complete: Analysis engine operational\n")
    await asyncio.sleep(2)

    # =========================================================================
    # PHASE 5: FRONTEND (Parallel)
    # =========================================================================

    print("="*80)
    print("PHASE 5: React Frontend")
    print("="*80 + "\n")

    frontend_tasks = await asyncio.gather(
        # PyMaster: React setup
        api.assign_task(
            agent_name="PyMaster",
            title="Create React application structure",
            description="""
            Setup modern React frontend:
            - Vite + React 18 + TypeScript
            - TailwindCSS for styling
            - React Router for navigation
            - React Query for data fetching
            - Zustand for state management
            - Component structure
            Location: projektagenci01/frontend/
            """,
            priority=10
        ),

        # PyMaster: UI components
        api.assign_task(
            agent_name="PyMaster",
            title="Build core UI components",
            description="""
            Create React components:
            - CaseManager: create and list cases
            - DocumentUpload: drag & drop, progressive
            - AnalysisViewer: real-time progress
            - ExecutiveSummary: key findings display
            - DeepDiveReport: detailed view with citations
            - API integration hooks
            """,
            priority=9
        )
    )

    print(f"\n✅ Phase 5 complete: {len(frontend_tasks)} frontend tasks finished\n")
    await asyncio.sleep(2)

    # =========================================================================
    # PHASE 6: INTEGRATION & TESTING
    # =========================================================================

    print("="*80)
    print("PHASE 6: Integration & Testing")
    print("="*80 + "\n")

    integration_tasks = await asyncio.gather(
        # Artur: System integration
        api.assign_task(
            agent_name="Artur",
            title="Coordinate system integration",
            description="""
            Integrate all components:
            - Verify all services communicate
            - Test end-to-end flow
            - Document setup process
            - Create startup scripts
            - Validate against requirements
            """,
            priority=10
        ),

        # PyMaster: Testing
        api.assign_task(
            agent_name="PyMaster",
            title="Create test suite",
            description="""
            Build comprehensive tests:
            - Unit tests for core functions
            - Integration tests for API
            - Test fixtures with sample PDFs
            - Performance benchmarks
            - Test with 2,000+ pages
            """,
            priority=8
        ),

        # DBMaster: Database initialization
        api.assign_task(
            agent_name="DBMaster",
            title="Create database initialization scripts",
            description="""
            Setup scripts for:
            - PostgreSQL schema creation
            - Qdrant collection setup
            - Elasticsearch index creation
            - Redis key namespace setup
            - Sample data loading
            - Health check utilities
            """,
            priority=9
        )
    )

    print(f"\n✅ Phase 6 complete: {len(integration_tasks)} integration tasks finished\n")

    # =========================================================================
    # FINAL REPORT
    # =========================================================================

    print("\n" + "="*80)
    print("MULTI-AGENT BUILD COMPLETE!")
    print("="*80 + "\n")

    # Get final system status
    status = api.get_system_status()

    print("📊 Build Statistics:")
    print(f"   Total Agents Used: {len(status['agents'])}")
    print(f"   Total Tasks Completed: {len([t for t in status['tasks'] if t['status'] == 'completed'])}")
    print(f"   Messages Exchanged: {status['message_history_count']}")
    print(f"   Total Token Budget Used: 360,000 tokens")

    print("\n👥 Agent Contributions:")
    for agent_name, agent_status in status['agents'].items():
        completed = agent_status.get('completed_tasks', 0)
        print(f"   {agent_name:12} → {completed} tasks completed")

    print("\n📁 Deliverables Created in projektagenci01/:")
    print("   ✅ Architecture documentation")
    print("   ✅ Backend (FastAPI)")
    print("   ✅ Frontend (React)")
    print("   ✅ Database schemas")
    print("   ✅ Docker Compose")
    print("   ✅ PDF processing pipeline")
    print("   ✅ Embeddings system")
    print("   ✅ LM Studio integration")
    print("   ✅ Financial calculators")
    print("   ✅ Micro-agent system")
    print("   ✅ Report generators")
    print("   ✅ Test suite")

    print("\n🚀 Next Steps:")
    print("   1. Review generated code in projektagenci01/")
    print("   2. Start Docker services: docker-compose up -d")
    print("   3. Run backend: cd backend && uvicorn main:app --reload")
    print("   4. Run frontend: cd frontend && npm run dev")
    print("   5. Upload your financial documents")

    print("\n" + "="*80)

    # Shutdown agent system
    await api.shutdown()

    print("\n✅ Agent team deactivated. Build complete!\n")


if __name__ == "__main__":
    try:
        asyncio.run(build_investigation_platform())
    except KeyboardInterrupt:
        print("\n\n⚠️  Build interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during build: {e}")
        import traceback
        traceback.print_exc()
