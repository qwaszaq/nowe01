"""
Example Usage of StateManager
Demonstrates common operations for document processing and analysis state tracking
"""

import asyncio
import time
from uuid import uuid4
from state_manager import StateManager, DocumentState, AnalysisState


# =========================================================================
# EXAMPLE 1: Document Processing Workflow
# =========================================================================

def example_document_processing():
    """Example: Track document through processing stages"""
    print("=" * 80)
    print("EXAMPLE 1: Document Processing Workflow")
    print("=" * 80)

    # Initialize state manager
    state_manager = StateManager()

    # Create sample document and case IDs
    case_id = uuid4()
    document_id = uuid4()

    print(f"\nProcessing document: {document_id}")
    print(f"Case: {case_id}\n")

    try:
        # Stage 1: Start processing
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.PENDING,
            metadata={"filename": "financial_report_2023.pdf", "case_id": str(case_id)},
            progress_percent=0
        )
        print("✓ Document queued for processing")

        # Stage 2: Extracting text
        time.sleep(1)
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.EXTRACTING,
            progress_percent=20
        )
        print("✓ Extracting text from PDF...")

        # Stage 3: Chunking
        time.sleep(1)
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.CHUNKING,
            progress_percent=40
        )
        print("✓ Chunking text into segments...")

        # Stage 4: Embedding
        time.sleep(1)
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.EMBEDDING,
            progress_percent=60
        )
        print("✓ Generating embeddings...")

        # Stage 5: Storing
        time.sleep(1)
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.STORING,
            progress_percent=80
        )
        print("✓ Storing in vector database...")

        # Stage 6: Complete
        time.sleep(1)
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.COMPLETED,
            progress_percent=100
        )
        print("✓ Document processing completed!\n")

        # Get final state
        final_state = state_manager.get_document_state(document_id)
        print(f"Final state: {final_state.state.value}")
        print(f"Progress: {final_state.progress_percent}%")
        print(f"Duration: {(final_state.updated_at - final_state.started_at).total_seconds():.2f}s")

    except Exception as e:
        print(f"✗ Error: {e}")

    finally:
        state_manager.close()


# =========================================================================
# EXAMPLE 2: Error Handling and Retry
# =========================================================================

def example_error_handling():
    """Example: Handle document processing failure and retry"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Error Handling and Retry")
    print("=" * 80)

    state_manager = StateManager()
    document_id = uuid4()

    try:
        # Start processing
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.PENDING,
            metadata={"filename": "corrupted_document.pdf"}
        )
        print(f"\nProcessing document: {document_id}")

        # Simulate extraction stage
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.EXTRACTING,
            progress_percent=20
        )
        print("✓ Extracting text...")

        # Simulate failure
        time.sleep(1)
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.FAILED,
            error_details="PDF extraction failed: File corrupted",
            progress_percent=20
        )
        print("✗ Processing failed: PDF extraction error")

        # Increment error counter
        state_manager.increment_error_count("extraction_error")

        # Retry failed documents
        print("\nRetrying failed documents...")
        retried = state_manager.retry_failed_documents(max_retries=3)
        print(f"✓ Queued {len(retried)} documents for retry")

        # Check state after retry
        state = state_manager.get_document_state(document_id)
        print(f"New state: {state.state.value}")
        print(f"Retry count: {state.retry_count}")

    except Exception as e:
        print(f"✗ Error: {e}")

    finally:
        state_manager.close()


# =========================================================================
# EXAMPLE 3: Analysis Workflow
# =========================================================================

def example_analysis_workflow():
    """Example: Track analysis workflow through stages"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Analysis Workflow")
    print("=" * 80)

    state_manager = StateManager()
    analysis_id = str(uuid4())
    case_id = uuid4()

    try:
        print(f"\nRunning analysis: {analysis_id}")
        print(f"Case: {case_id}\n")

        # Stage 1: Queue analysis
        state_manager.set_analysis_state(
            analysis_id=analysis_id,
            case_id=case_id,
            state=AnalysisState.QUEUED,
            progress_percent=0
        )
        print("✓ Analysis queued")

        # Stage 2: Searching documents
        time.sleep(1)
        state_manager.set_analysis_state(
            analysis_id=analysis_id,
            case_id=case_id,
            state=AnalysisState.SEARCHING,
            progress_percent=25,
            metadata={"documents_found": 15}
        )
        print("✓ Searching relevant documents...")

        # Stage 3: Calculating metrics
        time.sleep(1)
        state_manager.set_analysis_state(
            analysis_id=analysis_id,
            case_id=case_id,
            state=AnalysisState.CALCULATING,
            progress_percent=50,
            metadata={"metrics_calculated": 42}
        )
        print("✓ Calculating financial metrics...")

        # Stage 4: Classifying
        time.sleep(1)
        state_manager.set_analysis_state(
            analysis_id=analysis_id,
            case_id=case_id,
            state=AnalysisState.CLASSIFYING,
            progress_percent=75
        )
        print("✓ Classifying risk factors...")

        # Stage 5: Complete
        time.sleep(1)
        results = {
            "liquidity_score": 7.5,
            "risk_level": "moderate",
            "key_findings": ["Strong revenue growth", "High debt levels"]
        }
        state_manager.set_analysis_state(
            analysis_id=analysis_id,
            case_id=case_id,
            state=AnalysisState.COMPLETED,
            progress_percent=100,
            results=results
        )
        print("✓ Analysis completed!\n")

        # Get final results
        final_state = state_manager.get_analysis_state(analysis_id)
        print(f"Final state: {final_state.state.value}")
        print(f"Results: {final_state.results}")

    except Exception as e:
        print(f"✗ Error: {e}")

    finally:
        state_manager.close()


# =========================================================================
# EXAMPLE 4: Processing Statistics
# =========================================================================

def example_processing_stats():
    """Example: Get processing statistics and monitoring data"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Processing Statistics")
    print("=" * 80)

    state_manager = StateManager()

    try:
        # Get overall statistics
        stats = state_manager.get_processing_stats()

        print("\n📊 Processing Statistics")
        print("-" * 80)
        print(f"Total documents:     {stats.total_documents}")
        print(f"Completed:           {stats.completed} ({stats.success_rate:.1f}%)")
        print(f"Failed:              {stats.failed} ({stats.error_rate:.1f}%)")
        print(f"In progress:         {stats.pending + stats.extracting + stats.chunking + stats.embedding + stats.storing}")
        print(f"  - Pending:         {stats.pending}")
        print(f"  - Extracting:      {stats.extracting}")
        print(f"  - Chunking:        {stats.chunking}")
        print(f"  - Embedding:       {stats.embedding}")
        print(f"  - Storing:         {stats.storing}")

        if stats.avg_processing_time_seconds:
            print(f"\nAvg processing time: {stats.avg_processing_time_seconds:.2f}s")

        print("\n📈 Error Breakdown")
        print("-" * 80)
        for error_type, count in stats.errors_by_type.items():
            if count > 0:
                print(f"  {error_type}: {count}")

    except Exception as e:
        print(f"✗ Error: {e}")

    finally:
        state_manager.close()


# =========================================================================
# EXAMPLE 5: Real-time Monitoring
# =========================================================================

def example_realtime_monitoring():
    """Example: Subscribe to state changes and alerts"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Real-time Monitoring")
    print("=" * 80)

    state_manager = StateManager()

    # Define callbacks
    def on_state_change(event):
        """Handle state change events"""
        print(f"🔔 State Change: {event['entity_type']} {event['entity_id']}")
        print(f"   {event['old_state']} → {event['new_state']}")

    def on_alert(alert):
        """Handle alert events"""
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        emoji = severity_emoji.get(alert['severity'], "📢")
        print(f"{emoji} Alert: [{alert['severity'].upper()}] {alert['message']}")

    print("\n📡 Subscribing to events...")
    print("(This would run continuously in a real application)\n")

    # In a real application, you would run these in separate threads:
    # threading.Thread(target=state_manager.subscribe_to_state_changes, args=(on_state_change,)).start()
    # threading.Thread(target=state_manager.subscribe_to_alerts, args=(on_alert,)).start()

    print("Example subscription handlers defined:")
    print("  - on_state_change: Tracks all state transitions")
    print("  - on_alert: Monitors system alerts")


# =========================================================================
# EXAMPLE 6: Batch Operations
# =========================================================================

def example_batch_operations():
    """Example: Process multiple documents and track overall progress"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Batch Operations")
    print("=" * 80)

    state_manager = StateManager()
    case_id = uuid4()

    # Simulate processing multiple documents
    document_ids = [uuid4() for _ in range(5)]

    print(f"\n📦 Processing batch of {len(document_ids)} documents")
    print(f"Case: {case_id}\n")

    try:
        # Queue all documents
        for i, doc_id in enumerate(document_ids):
            state_manager.set_document_state(
                document_id=doc_id,
                state=DocumentState.PENDING,
                metadata={"filename": f"document_{i+1}.pdf", "case_id": str(case_id)}
            )
            print(f"✓ Queued document {i+1}/{len(document_ids)}")

        # Simulate processing (simplified)
        print("\n🔄 Processing documents...")
        for doc_id in document_ids[:3]:  # Complete 3
            state_manager.set_document_state(doc_id, DocumentState.EXTRACTING)
            state_manager.set_document_state(doc_id, DocumentState.CHUNKING)
            state_manager.set_document_state(doc_id, DocumentState.EMBEDDING)
            state_manager.set_document_state(doc_id, DocumentState.STORING)
            state_manager.set_document_state(doc_id, DocumentState.COMPLETED, progress_percent=100)

        # Fail 1
        state_manager.set_document_state(
            document_ids[3],
            DocumentState.FAILED,
            error_details="Network timeout"
        )

        # Leave 1 in progress
        state_manager.set_document_state(document_ids[4], DocumentState.CHUNKING, progress_percent=40)

        # Get case statistics
        stats = state_manager.get_processing_stats(case_id=case_id)
        print(f"\n📊 Batch Processing Results")
        print("-" * 80)
        print(f"Total:     {stats.total_documents}")
        print(f"Completed: {stats.completed} ({stats.success_rate:.1f}%)")
        print(f"Failed:    {stats.failed}")
        print(f"Active:    {stats.chunking + stats.embedding + stats.storing}")

    except Exception as e:
        print(f"✗ Error: {e}")

    finally:
        state_manager.close()


# =========================================================================
# RUN ALL EXAMPLES
# =========================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("STATE MANAGER EXAMPLES")
    print("=" * 80)

    # Run examples
    example_document_processing()
    example_error_handling()
    example_analysis_workflow()
    example_processing_stats()
    example_realtime_monitoring()
    example_batch_operations()

    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80)
