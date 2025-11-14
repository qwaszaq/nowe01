# 🛡️ DEVELOPMENT GUARDRAILS

**Status**: MANDATORY FOR ALL DEVELOPMENT
**Last Updated**: 2025-11-14
**Enforcement**: Code reviews, CI/CD checks, deployment blockers

---

## What Are Guardrails?

**Guardrails** are **non-negotiable architectural principles** that protect the system's integrity.

They are NOT:
- ❌ Suggestions
- ❌ Best practices
- ❌ Guidelines
- ❌ Recommendations

They ARE:
- ✅ **Deployment blockers** (violations prevent release)
- ✅ **Architecture constraints** (cannot be bypassed)
- ✅ **Quality guarantees** (enforced by code)
- ✅ **Team agreements** (everyone follows)

**Violating a guardrail requires explicit architecture review and approval.**

---

## GUARDRAIL #1: DATA QUALITY IS GUARANTEED 🛡️

### The Principle

> **"This system will NEVER silently store incorrect financial data"**

### Why This Exists

Financial data drives critical business decisions. **Silent data corruption is catastrophic.**

**Real-world impact**:
- 2023 data requested → 2022 data returned → **Wrong financial decisions**
- Scanned PDF processed → Garbage output → **Unreliable system**
- Empty table stored → Query returns null → **Missing insights**

### The Guarantee

**Every piece of data that enters the database has been**:
1. ✅ Validated for PDF format quality
2. ✅ Validated for extraction quality
3. ✅ Validated for table structure
4. ✅ Validated for semantic correctness
5. ✅ Scored for quality (0-100%)
6. ✅ **Rejected if ANY critical issue found**

### Implementation Requirements

**MANDATORY**: Use `ValidatedDoclingStorageAgent` for ALL document processing

```python
# ❌ FORBIDDEN - Bypasses quality validation
from src.core.llm.docling_storage_agent import DoclingStorageAgent
agent = DoclingStorageAgent(postgres)

# ✅ REQUIRED - Enforces quality validation
from src.core.llm.validated_docling_storage_agent import ValidatedDoclingStorageAgent
agent = ValidatedDoclingStorageAgent(
    postgres_store=postgres,
    strict_mode=True,           # REQUIRED: Reject on errors
    min_table_quality=50.0,     # REQUIRED: Minimum 50% quality
    require_digital_pdf=True    # REQUIRED: Reject scanned PDFs
)
```

### Enforcement

**Code Review Checklist**:
- [ ] Does code store tables in database?
- [ ] Does it use `ValidatedDoclingStorageAgent`?
- [ ] Does it check quality reports?
- [ ] Does it handle rejections properly?

**CI/CD Checks**:
- [ ] No direct imports of `DoclingStorageAgent`
- [ ] All table storage goes through validation
- [ ] Quality reports logged
- [ ] Test coverage for rejection scenarios

**Deployment Blockers**:
- ❌ Any code that bypasses validation
- ❌ Any code that ignores quality scores
- ❌ Any code that silently accepts failures

### Exceptions

**There are NO exceptions to this guardrail.**

Even for:
- ❌ "Quick fixes"
- ❌ "Temporary workarounds"
- ❌ "Legacy code"
- ❌ "Internal testing"

**If validation fails, fix the validation OR fix the data. Never bypass.**

### Documentation

- **Full Guide**: `/backend/docs/DATA_QUALITY_GUARANTEES.md`
- **Summary**: `/backend/docs/QUALITY_GUARANTEES_SUMMARY.md`
- **Code**: `/backend/src/validation/`

---

## GUARDRAIL #2: MICROAGENT + DOCLING ARCHITECTURE 🏗️

### The Principle

> **"ALL financial metric extraction MUST use the Microagent + Docling approach"**

### Why This Exists

**Previous approach (REMOVED)**:
- ❌ Semantic search with vector embeddings
- ❌ Averaged random numbers from unrelated chunks
- ❌ Produced INCORRECT financial values
- ❌ NO source traceability

**Current approach (REQUIRED)**:
- ✅ Docling: Structure-aware PDF table extraction
- ✅ Microagents: Specialized agents for specific tasks
- ✅ Python logic: Deterministic row/column matching
- ✅ Source tracking: Full provenance

### Implementation Requirements

**MANDATORY Components**:
1. **Docling**: Extract tables with structure preservation
2. **Table matching**: Find correct table by statement type
3. **Row/column logic**: Extract exact value from [row, col] intersection
4. **Source tracking**: Document, page, table, row, column

**Code Structure**:
```python
# ✅ REQUIRED: Use FinancialExtractionAgent pattern
agent = FinancialExtractionAgent(redis, postgres, llm)
result = await agent.extract_metric(
    case_id=case_id,
    metric_name="Aktywa razem",
    year="2023"
)
# Returns: {value, unit, source, confidence}
```

### Forbidden Approaches

**❌ FORBIDDEN**: Semantic search for financial metrics
```python
# ❌ DO NOT DO THIS
embeddings = embed("Aktywa razem 2023")
results = qdrant.search(embeddings, top_k=10)
values = [parse_number(r.content) for r in results]
return sum(values) / len(values)  # ❌ WRONG! Averages random numbers
```

**❌ FORBIDDEN**: LLM-based extraction without structure
```python
# ❌ DO NOT DO THIS
prompt = f"Extract Aktywa razem for 2023: {document_text}"
response = llm.chat(prompt)
return parse_number(response)  # ❌ WRONG! No structure, no provenance
```

### Enforcement

**Code Review Checklist**:
- [ ] Uses Docling for table extraction?
- [ ] Uses microagent pattern?
- [ ] Extracts from [row, col] intersection?
- [ ] Returns source provenance?
- [ ] NO semantic search for metrics?
- [ ] NO LLM-based number extraction?

**No Fallback Allowed**:
```python
# ❌ FORBIDDEN
try:
    result = financial_agent.extract_metric(...)
except Exception:
    # ❌ DO NOT fall back to semantic search
    result = semantic_search_fallback(...)  # FORBIDDEN
```

**If the microagent fails, the system fails. Fix the microagent, don't create workarounds.**

### Documentation

- **Architecture**: `/backend/docs/ARCHITECTURE.md`
- **Code**: `/backend/src/core/llm/financial_extraction_agent.py`

---

## GUARDRAIL #3: EXPLICIT FAILURES OVER SILENT FAILURES ⚠️

### The Principle

> **"Fail loud, not silent. Users must know when things go wrong"**

### Why This Exists

**Silent failures are catastrophic**:
- User uploads document → Processing "succeeds" → Actually failed → User trusts bad data
- Query returns null → User assumes no data → Actually extraction error
- Wrong year data stored → User makes decisions on wrong data → Financial impact

### Implementation Requirements

**MANDATORY: Explicit error handling**

```python
# ❌ FORBIDDEN - Silent failure
try:
    result = extract_metric(...)
except Exception as e:
    logger.error(f"Failed: {e}")  # ❌ Logged but user never knows
    return None  # ❌ Silent failure

# ✅ REQUIRED - Explicit failure
try:
    result = extract_metric(...)
except Exception as e:
    logger.error(f"Failed: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail=f"Metric extraction failed: {str(e)}"  # ✅ User sees error
    )
```

**MANDATORY: Quality reports returned to user**

```python
# ✅ REQUIRED - Return quality info
result = await agent.store_document_tables(doc_id, file_path)

return {
    "success": result["success"],
    "tables_stored": result["tables_stored"],
    "tables_rejected": result["tables_rejected"],
    "quality_score": result["overall_quality_score"],
    "rejection_reasons": result["rejection_reasons"],  # ✅ User sees why
    "warnings": result["warnings"]
}
```

### Enforcement

**Code Review Checklist**:
- [ ] Are exceptions properly raised?
- [ ] Are users informed of failures?
- [ ] Are quality issues visible to users?
- [ ] Are warnings logged AND returned?

**Forbidden Patterns**:
- ❌ `except: pass` (silent swallowing)
- ❌ `return None` on error (ambiguous)
- ❌ Logging only (user unaware)

---

## GUARDRAIL #4: IMMUTABLE AUDIT TRAIL 📝

### The Principle

> **"Every data operation must be fully traceable"**

### Why This Exists

For compliance, debugging, and trust:
- **Who** performed the operation?
- **When** did it happen?
- **What** was changed?
- **Why** did it change (rejection reason, quality score)?
- **Where** did it come from (source document, page, table)?

### Implementation Requirements

**MANDATORY: Source tracking in extracted data**

```python
{
    "value": 21654160,
    "source": {
        "document_id": "uuid",
        "document_name": "Grupa_Azoty_2023.pdf",
        "page_number": 42,
        "table_caption": "Bilans na 31.12.2023",
        "row_label": "Aktywa razem",
        "column_label": "2023"
    }
}
```

**MANDATORY: Quality tracking in database**

```sql
ALTER TABLE extracted_tables
ADD COLUMN quality_score FLOAT,
ADD COLUMN quality_level VARCHAR(1),
ADD COLUMN quality_report JSONB,
ADD COLUMN validation_timestamp TIMESTAMP;
```

**MANDATORY: Operation logging**

```python
logger.info(
    f"Table stored: doc={doc_id}, page={page_num}, "
    f"quality={quality_score:.1f}%, year={year}"
)

logger.warning(
    f"Table rejected: doc={doc_id}, page={page_num}, "
    f"reason={rejection_reason}"
)
```

### Enforcement

**Code Review Checklist**:
- [ ] Does extracted data include source?
- [ ] Are quality scores stored?
- [ ] Are operations logged?
- [ ] Can we trace data back to source?

---

## GUARDRAIL #5: NO PREMATURE OPTIMIZATION ⚡

### The Principle

> **"Accuracy first, speed second. Never sacrifice correctness for performance"**

### Why This Exists

**Performance optimizations often introduce bugs**:
- Caching → Stale data
- Parallelization → Race conditions
- Batching → Partial failures
- Shortcuts → Wrong results

### Implementation Requirements

**MANDATORY: Measure before optimizing**

```python
# ❌ FORBIDDEN - Premature optimization
# "I think this is slow, let me cache it"
cache.set(key, value)  # ❌ Might return stale data

# ✅ REQUIRED - Measure first
import time
start = time.time()
result = expensive_operation()
elapsed = time.time() - start

if elapsed > 5.0:
    logger.warning(f"Slow operation: {elapsed:.2f}s")
    # NOW consider optimization, with proper invalidation
```

**MANDATORY: Profile before changing**

- ✅ Use `cProfile`, `line_profiler`, or similar
- ✅ Identify actual bottlenecks
- ✅ Benchmark before/after
- ✅ Verify correctness maintained

### Forbidden Optimizations

**❌ FORBIDDEN without profiling**:
- Caching without invalidation strategy
- Parallel processing without testing
- Skipping validation "for speed"
- Approximations instead of exact values

### Enforcement

**Code Review Checklist**:
- [ ] Is there profiling data supporting this optimization?
- [ ] Are correctness tests passing?
- [ ] Is the speedup measured?
- [ ] Are edge cases still handled?

---

## GUARDRAIL #6: TEST COVERAGE FOR CRITICAL PATHS 🧪

### The Principle

> **"All data extraction and storage paths must have tests"**

### Why This Exists

Financial data cannot be "mostly correct" - it must be **exactly correct**.

### Implementation Requirements

**MANDATORY: Test types**

1. **Unit Tests**: Logic without external dependencies
2. **Integration Tests**: Real PDF → Docling → Agent → Verified value
3. **Validation Tests**: Quality validators with edge cases
4. **Regression Tests**: Known values from real documents

**MANDATORY: Coverage thresholds**

- Validators: **100% coverage**
- Extraction agents: **90% coverage**
- API endpoints: **80% coverage**

**Example Test**:
```python
def test_quality_validation_rejects_empty_table():
    """Verify empty tables are rejected"""
    table = {"headers": [], "rows": []}
    result = validate_table_quality(table)

    assert not result.passed
    assert result.quality_score == 0
    assert any(
        issue.code == "TABLE_NO_ROWS"
        for issue in result.issues
    )
```

### Enforcement

**Code Review Checklist**:
- [ ] Are there tests for new extraction logic?
- [ ] Are validation scenarios covered?
- [ ] Are rejection paths tested?
- [ ] Do tests use real financial data?

**CI/CD Requirements**:
- ✅ All tests pass before merge
- ✅ Coverage thresholds met
- ✅ No regressions introduced

---

## GUARDRAIL VIOLATIONS: HOW TO HANDLE

### If You Need to Violate a Guardrail

**Process**:
1. Document **why** the guardrail prevents your solution
2. Propose **alternative approaches** that respect the guardrail
3. If no alternative exists, request **architecture review**
4. Get **explicit approval** from tech lead
5. Document the **exception** and **timeline** for remediation

**Examples of valid exceptions**:
- ✅ Emergency hotfix (with immediate follow-up to fix properly)
- ✅ Prototype/research code (clearly marked, not in production)
- ✅ Deprecation period (with clear migration plan)

**Examples of invalid exceptions**:
- ❌ "It's faster this way"
- ❌ "I don't have time to do it right"
- ❌ "It's just for testing"
- ❌ "The guardrail is wrong" (without proposing better alternative)

### If You See a Guardrail Violation

**Immediate actions**:
1. 🚨 Flag in code review (blocking comment)
2. 📝 Document the violation
3. 👥 Tag tech lead

**Do NOT**:
- ❌ Approve "just this once"
- ❌ Accept "will fix later"
- ❌ Allow "temporary workaround"

**Guardrails exist for a reason. Violations compound into technical debt.**

---

## SUMMARY: THE 6 GUARDRAILS

| # | Guardrail | Enforcement |
|---|-----------|-------------|
| 1 | **Data Quality Guaranteed** | Use ValidatedDoclingStorageAgent |
| 2 | **Microagent + Docling Architecture** | No semantic search for metrics |
| 3 | **Explicit Failures** | Raise exceptions, return quality reports |
| 4 | **Immutable Audit Trail** | Source tracking + logging |
| 5 | **No Premature Optimization** | Profile before optimizing |
| 6 | **Test Coverage** | 90%+ for critical paths |

---

## RELATED DOCUMENTS

- **Architecture**: `/backend/docs/ARCHITECTURE.md`
- **Quality Guarantees**: `/backend/docs/DATA_QUALITY_GUARANTEES.md`
- **Quality Summary**: `/backend/docs/QUALITY_GUARANTEES_SUMMARY.md`
- **This Document**: `/backend/docs/DEVELOPMENT_GUARDRAILS.md`

---

**Questions?** Ask in team channel or create GitHub discussion.

**Violations?** Flag immediately in code review.

**Last Updated**: 2025-11-14
**Status**: MANDATORY - ACTIVELY ENFORCED
