# 🛡️ Quality Guarantee - Quick Reference

**Print this. Keep it visible. Reference it daily.**

---

## ⚡ THE ONE-LINE RULE

> **"Would I trust this with my own money? If not, fix it."**

---

## 🚫 NEVER DO THIS

```python
# ❌ Silent failures
except Exception:
    pass  # FORBIDDEN

# ❌ Bypass validation
agent = DoclingStorageAgent(postgres)  # FORBIDDEN - no validation

# ❌ Ignore quality
result = extract(pdf)
# Store without checking quality  # FORBIDDEN

# ❌ Return None on error
except Exception:
    return None  # FORBIDDEN - user unaware
```

---

## ✅ ALWAYS DO THIS

```python
# ✅ Use validated agent
from src.core.llm.validated_docling_storage_agent import ValidatedDoclingStorageAgent
agent = ValidatedDoclingStorageAgent(
    postgres_store=postgres,
    strict_mode=True,
    min_table_quality=50.0,
    require_digital_pdf=True
)

# ✅ Check quality reports
result = await agent.store_document_tables(doc_id, file_path)
if not result["success"]:
    raise HTTPException(
        status_code=422,
        detail=result["rejection_reasons"]
    )

# ✅ Explicit errors
try:
    result = extract_metric(...)
except Exception as e:
    logger.error(f"Extraction failed: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))

# ✅ Return quality info
return {
    "value": result["value"],
    "quality_score": result["quality_score"],
    "source": result["source"]
}
```

---

## 🎯 THE 3 QUESTIONS

Before committing, ask:

### 1. **Can this silently store bad data?**
- ❌ Yes → **BLOCK**
- ✅ No → Continue

### 2. **Will the user know if this fails?**
- ❌ No → **BLOCK**
- ✅ Yes → Continue

### 3. **Can we trace this data to its source?**
- ❌ No → **BLOCK**
- ✅ Yes → Ship it

---

## 📋 CODE REVIEW CHECKLIST

```
Quality Validation:
[ ] Uses ValidatedDoclingStorageAgent
[ ] Checks quality reports
[ ] Handles rejections
[ ] No validation bypasses

Error Handling:
[ ] Exceptions are raised (not swallowed)
[ ] User sees failures (not just logs)
[ ] Errors are actionable
[ ] No silent failures

Source Tracking:
[ ] Document ID included
[ ] Page number included
[ ] Table/row/column reference
[ ] Confidence score included

Testing:
[ ] Unit tests for logic
[ ] Integration tests for pipeline
[ ] Edge cases covered
[ ] Real data tested
```

---

## 🚨 QUALITY VIOLATIONS

### FORBIDDEN PATTERNS

```python
# 1. Silent swallowing
try:
    risky_operation()
except:
    pass  # ❌ FORBIDDEN

# 2. Lying to user
except Exception:
    return {"success": True}  # ❌ FORBIDDEN

# 3. Validation bypass
if quick_mode:
    skip_validation()  # ❌ FORBIDDEN

# 4. No source tracking
return {"value": 12345}  # ❌ FORBIDDEN (no source)

# 5. Ignoring quality score
result = agent.extract(pdf)
store(result)  # ❌ FORBIDDEN (didn't check quality)
```

### FIX IMMEDIATELY

If you see ANY of these in code review → **BLOCK MERGE**

---

## 📊 QUALITY LEVELS

| Grade | Score | Action |
|-------|-------|--------|
| **A** | 90-100% | ✅ Auto-approve |
| **B** | 70-89% | ⚠️ Use with warnings |
| **C** | 50-69% | 🔍 Review required |
| **D** | 30-49% | 🚫 Manual review |
| **F** | 0-29% | ❌ REJECT |

**Rule**: If quality < 50%, **REJECT IMMEDIATELY**

---

## 🛠️ DEBUGGING CHECKLIST

### Upload Failed?

```python
# Check PDF quality
from src.validation import validate_pdf_quality
pdf_report = validate_pdf_quality(pdf_path, require_digital=True)
print(pdf_report)

# Check logs
# Look for: "PDF_SCANNED", "PDF_ENCRYPTED", "PDF_TOO_LARGE"
```

### Table Rejected?

```python
# Check table quality
from src.validation import validate_table_quality
table_report = validate_table_quality(table, is_financial=True)
print(f"Score: {table_report.quality_score}")
print(f"Issues: {table_report.issues}")

# Check logs
# Look for: "TABLE_NO_ROWS", "TABLE_EMPTY_HEADERS", "TABLE_HIGH_EMPTY_CELLS"
```

### Year Mismatch?

```python
# Check semantic validation
from src.validation import validate_semantic_content
semantic_report = validate_semantic_content(
    table,
    extracted_metadata={"extracted_year": "2023"},
    expected_metadata={"expected_year": "2024"}
)
print(f"Issues: {semantic_report.issues}")

# Check logs
# Look for: "SEMANTIC_YEAR_MISMATCH"
```

---

## 📚 RELATED DOCS

**Full Documentation**:
- 📖 [Data Quality Guarantees](/backend/docs/DATA_QUALITY_GUARANTEES.md) - Complete guide
- 📄 [Quality Summary](/backend/docs/QUALITY_GUARANTEES_SUMMARY.md) - Executive summary
- 🛡️ [Development Guardrails](/backend/docs/DEVELOPMENT_GUARDRAILS.md) - Enforcement rules
- 💭 [Quality Principles](/backend/docs/QUALITY_FIRST_PRINCIPLES.md) - Philosophy
- 🏗️ [Architecture](/backend/docs/ARCHITECTURE.md) - System design

**Quick Access**:
- This document: `/backend/docs/QUALITY_QUICK_REFERENCE.md`

---

## 💡 QUICK TIPS

### ✅ DO

- Validate BEFORE storing
- Raise exceptions on failure
- Return quality scores
- Track data sources
- Test edge cases
- Ask "would I trust this?"

### ❌ DON'T

- Skip validation "just this once"
- Swallow exceptions
- Return None on error
- Store without provenance
- Assume "it usually works"
- Ship without testing

---

## 🚀 GETTING STARTED

### 1. Read This First
```
[ ] Quality Quick Reference (this doc) ← YOU ARE HERE
[ ] Data Quality Guarantees (full guide)
[ ] Development Guardrails (enforcement)
```

### 2. Update Your Code
```python
# Replace
from src.core.llm.docling_storage_agent import DoclingStorageAgent

# With
from src.core.llm.validated_docling_storage_agent import ValidatedDoclingStorageAgent
```

### 3. Test Your Changes
```bash
# Run quality validation tests
pytest tests/test_quality_validation.py -v

# Check coverage
pytest --cov=src/validation --cov-report=html
```

### 4. Review Checklist
```
[ ] Used ValidatedDoclingStorageAgent
[ ] Checked quality reports
[ ] Handled rejections
[ ] Added tests
[ ] Documented changes
```

---

## 📞 NEED HELP?

**Quality validation failing?**
1. Check logs for specific error codes
2. Review quality report JSON
3. Consult full documentation
4. Ask in team channel

**Unsure if code meets standards?**
1. Run the 3 questions test
2. Check the code review checklist
3. Request early code review
4. Ask for architecture guidance

---

## 🎯 REMEMBER

1. **Quality is not optional**
2. **Silent failures are bugs**
3. **Users must see quality**
4. **Trace every value to source**
5. **Correctness before speed**

---

**Last Updated**: 2025-11-14
**Print Date**: _____________
**Keep Visible**: Yes
**Reference Daily**: Yes

🛡️ **QUALITY GUARANTEED** 🛡️
