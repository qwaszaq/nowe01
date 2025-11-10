# Analysis Flow Usage Examples

## Overview

The `AnalysisFlow` orchestrator coordinates semantic search, financial calculators, micro-agents, and storage layers to perform comprehensive financial document analysis.

## Setup

```python
from uuid import UUID
from src.orchestration import create_analysis_flow, AnalysisFlow
from src.core.search.semantic_search import SemanticSearch
from src.core.llm.micro_agents import create_micro_agents
from src.storage.postgres_store import PostgresStore
from src.storage.redis_store import RedisStore

# Initialize dependencies
postgres = PostgresStore()
redis = RedisStore()
semantic_search = SemanticSearch(embeddings_service, qdrant_store)
micro_agents = create_micro_agents(redis, llm_client)

# Create orchestrator
flow = create_analysis_flow(
    semantic_search=semantic_search,
    micro_agents=micro_agents,
    postgres_store=postgres,
    redis_store=redis
)
```

## Analysis Types

### 1. Comprehensive Analysis (All 19 Ratios + Micro-Agents)

```python
# Full analysis with all ratios and AI insights
result = await flow.analyze_document(
    document_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    analysis_type="comprehensive"
)

# Access results
print(f"Quality Score: {result.quality_score}%")
print(f"Calculated Ratios: {result.metrics.total_calculated}/19")
print(f"Risk Assessment: {result.insights.risk_assessment}")
print(f"Liquidity Position: {result.insights.liquidity_position}")

# Liquidity ratios
for ratio in result.metrics.liquidity_ratios:
    print(f"{ratio.metric_name}: {ratio.metric_value} - {ratio.interpretation}")

# Profitability ratios
for ratio in result.metrics.profitability_ratios:
    print(f"{ratio.metric_name}: {ratio.metric_value}% - {ratio.interpretation}")

# Leverage ratios
for ratio in result.metrics.leverage_ratios:
    print(f"{ratio.metric_name}: {ratio.metric_value} - {ratio.interpretation}")

# Insights
print(f"\nKey Concerns:")
for concern in result.insights.key_concerns:
    print(f"  - {concern}")

print(f"\nKey Strengths:")
for strength in result.insights.key_strengths:
    print(f"  + {strength}")
```

**Output Example:**
```
Quality Score: 84.5%
Calculated Ratios: 16/19
Risk Assessment: low
Liquidity Position: strong

current_ratio: 2.35 - Strong liquidity (2.35). Company has $2.35 in current assets for every $1 of current liabilities.
quick_ratio: 1.82 - Excellent liquidity (1.82). Company can meet obligations without selling inventory.
cash_ratio: 0.68 - Strong cash position (0.68). Substantial cash reserves provide flexibility.

gross_margin: 45.2% - Strong margin (45.2%). Healthy profitability with good cost management.
net_margin: 12.8% - Strong profitability (12.8%). Healthy bottom line.
roe: 18.5% - Strong ROE (18.5%). Excellent returns meeting Warren Buffett's 15% threshold.

debt_to_equity: 0.65 - Moderate leverage (0.65). Balanced capital structure.

Key Concerns:
  - None identified

Key Strengths:
  + Strong liquidity position (current ratio > 2.0)
  + Excellent cash reserves (cash ratio > 0.5)
  + Outstanding ROE (> 15%)
```

---

### 2. Liquidity Analysis Only (5 Ratios)

```python
# Focus on short-term financial health
result = await flow.analyze_document(
    document_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    analysis_type="liquidity"
)

# Access liquidity metrics
for ratio in result.metrics.liquidity_ratios:
    print(f"{ratio.metric_name}: {ratio.metric_value}")
    print(f"  {ratio.interpretation}")
    print(f"  Citation: Pages {ratio.citation_data['page_numbers']}")
```

**Output Example:**
```
current_ratio: 2.35
  Strong liquidity (2.35). Company has $2.35 in current assets for every $1 of current liabilities.
  Citation: Pages [3, 5]

quick_ratio: 1.82
  Excellent liquidity (1.82). Company can meet obligations without selling inventory.
  Citation: Pages [3, 5, 8]

cash_ratio: 0.68
  Strong cash position (0.68). Substantial cash reserves provide flexibility.
  Citation: Pages [3, 12]

operating_cash_flow_ratio: 1.15
  Excellent cash generation (1.15). Operations produce more than enough cash.
  Citation: Pages [15]
```

---

### 3. Profitability Analysis Only (8 Ratios)

```python
# Focus on earnings generation
result = await flow.analyze_document(
    document_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    analysis_type="profitability"
)

# Compare margins
margins = {
    'Gross Margin': next((r.metric_value for r in result.metrics.profitability_ratios if r.metric_name == 'gross_margin'), None),
    'Operating Margin': next((r.metric_value for r in result.metrics.profitability_ratios if r.metric_name == 'operating_margin'), None),
    'Net Margin': next((r.metric_value for r in result.metrics.profitability_ratios if r.metric_name == 'net_margin'), None)
}

for margin_type, value in margins.items():
    print(f"{margin_type}: {value}%")
```

**Output Example:**
```
Gross Margin: 45.2%
Operating Margin: 18.3%
Net Margin: 12.8%

roa: 8.5% - Strong ROA. Effective asset management.
roe: 18.5% - Strong ROE. Excellent returns.
roic: 14.2% - Strong ROIC. Good capital efficiency.
asset_turnover: 1.42 - Good asset turnover. Healthy asset utilization.
```

---

### 4. Leverage Analysis Only (6 Ratios)

```python
# Focus on debt levels and financial risk
result = await flow.analyze_document(
    document_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    analysis_type="leverage"
)

# Check debt safety
for ratio in result.metrics.leverage_ratios:
    if ratio.metric_name in ['debt_to_equity', 'interest_coverage', 'debt_to_assets']:
        print(f"{ratio.metric_name}: {ratio.metric_value}")
        print(f"  {ratio.interpretation}\n")
```

**Output Example:**
```
debt_to_equity: 0.65
  Moderate leverage (0.65). Balanced capital structure.

debt_to_assets: 0.39
  Moderate leverage (0.39 or 39.0%). Balanced capital structure. 61.0% equity provides good cushion.

interest_coverage: 12.5
  Excellent coverage (12.5x). Strong debt safety. Earnings cover interest 12.5 times.

equity_multiplier: 1.65
  Low leverage (1.65x). Conservative financing.
```

---

### 5. Quick Analysis (Key Ratios Only)

```python
# Fast analysis with 3 key ratios
result = await flow.analyze_document(
    document_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    analysis_type="quick"
)

# Display key metrics
print(f"Current Ratio: {result.metrics.liquidity_ratios[0].metric_value}")
print(f"ROE: {result.metrics.profitability_ratios[0].metric_value}%")
print(f"Debt-to-Equity: {result.metrics.leverage_ratios[0].metric_value}")
print(f"\nAnalysis completed in: {result.metrics.calculation_time_ms:.0f}ms")
```

**Output Example:**
```
Current Ratio: 2.35
ROE: 18.5%
Debt-to-Equity: 0.65

Analysis completed in: 342ms
```

---

## Case-Level Query

### Search Across All Documents in a Case

```python
# Natural language search across case documents
results = await flow.query_case(
    case_id=UUID("abc12345-def6-7890-ghij-klmnopqrstuv"),
    query="What is the company's revenue growth trend?",
    context_window=2  # Include 2 chunks before/after matches
)

# Process results
for i, result in enumerate(results[:5], 1):
    print(f"\n{i}. Document {result.document_id} - Page {result.page_num}")
    print(f"   Score: {result.score:.3f}")
    print(f"   Text: {result.text[:200]}...")

    if result.context:
        print(f"   Context chunks: {len(result.context['before'])} before, {len(result.context['after'])} after")
```

**Output Example:**
```
1. Document 123e4567-e89b-12d3-a456-426614174000 - Page 8
   Score: 0.892
   Text: Revenue increased by 22.5% year-over-year, driven by strong demand in the technology sector. Q4 revenue reached $125M, representing the highest quarterly revenue in company history...
   Context chunks: 2 before, 2 after

2. Document 234f5678-f90c-23e4-b567-537725185001 - Page 12
   Score: 0.856
   Text: Three-year revenue CAGR of 18.2% demonstrates consistent growth trajectory. Market share expanded from 12% to 15.5% during the same period...
   Context chunks: 2 before, 1 after
```

---

## Calculate Metrics from Custom Data

### Direct Calculation Without Document

```python
# Provide financial data directly
financial_data = {
    'current_assets': 2_500_000,
    'current_liabilities': 1_200_000,
    'total_assets': 8_000_000,
    'total_equity': 4_500_000,
    'total_debt': 2_800_000,
    'revenue': 12_000_000,
    'gross_profit': 5_400_000,
    'operating_income': 2_200_000,
    'net_income': 1_600_000,
    'cash': 800_000,
    'inventory': 600_000,
    'operating_cash_flow': 1_400_000
}

# Calculate all applicable ratios
metrics = await flow.calculate_metrics_from_data(financial_data)

# Display results by category
print(f"LIQUIDITY RATIOS ({len(metrics.liquidity_ratios)} calculated)")
for ratio in metrics.liquidity_ratios:
    if ratio.metric_value:
        print(f"  {ratio.metric_name}: {ratio.metric_value}")

print(f"\nPROFITABILITY RATIOS ({len(metrics.profitability_ratios)} calculated)")
for ratio in metrics.profitability_ratios:
    if ratio.metric_value:
        print(f"  {ratio.metric_name}: {ratio.metric_value}%")

print(f"\nLEVERAGE RATIOS ({len(metrics.leverage_ratios)} calculated)")
for ratio in metrics.leverage_ratios:
    if ratio.metric_value:
        print(f"  {ratio.metric_name}: {ratio.metric_value}")

print(f"\nCalculation Time: {metrics.calculation_time_ms:.0f}ms")
print(f"Success Rate: {metrics.total_calculated}/{metrics.total_calculated + metrics.total_failed}")
```

**Output Example:**
```
LIQUIDITY RATIOS (4 calculated)
  current_ratio: 2.08
  quick_ratio: 1.58
  cash_ratio: 0.67
  operating_cash_flow_ratio: 1.17

PROFITABILITY RATIOS (6 calculated)
  gross_margin: 45.0%
  operating_margin: 18.33%
  net_margin: 13.33%
  roa: 20.0%
  roe: 35.56%
  asset_turnover: 1.5

LEVERAGE RATIOS (3 calculated)
  debt_to_equity: 0.62
  debt_to_assets: 0.35
  equity_multiplier: 1.78

Calculation Time: 28ms
Success Rate: 13/14
```

---

## Generate Insights from Stored Metrics

### AI-Powered Classification and Analysis

```python
# Generate insights for previously analyzed document
insights = await flow.generate_insights(
    document_id=UUID("123e4567-e89b-12d3-a456-426614174000")
)

# Display comprehensive insights
print("FINANCIAL HEALTH ASSESSMENT")
print("=" * 50)
print(f"Overall Health: {insights.overall_health.upper()}")
print(f"Risk Level: {insights.risk_assessment}")
print(f"Liquidity: {insights.liquidity_position}")
print(f"Leverage: {insights.leverage_analysis}")
print(f"Profitability Trend: {insights.profitability_trends}")

print(f"\nCLASSIFICATIONS RUN: {insights.classification_count}")

if insights.key_concerns:
    print("\nKEY CONCERNS:")
    for concern in insights.key_concerns:
        print(f"  ⚠️  {concern}")

if insights.key_strengths:
    print("\nKEY STRENGTHS:")
    for strength in insights.key_strengths:
        print(f"  ✅ {strength}")
```

**Output Example:**
```
FINANCIAL HEALTH ASSESSMENT
==================================================
Overall Health: GOOD
Risk Level: low
Liquidity: strong
Leverage: moderate
Profitability Trend: stable

CLASSIFICATIONS RUN: 3

KEY STRENGTHS:
  ✅ Strong liquidity position (current ratio > 2.0)
  ✅ Excellent cash reserves (cash ratio > 0.5)
  ✅ Outstanding ROE (> 20%)
  ✅ Conservative leverage (D/E < 0.5)
```

---

## Caching Behavior

### Cache Hit Example

```python
import time

# First call - cache miss
start = time.time()
result1 = await flow.analyze_document(
    document_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    analysis_type="comprehensive"
)
elapsed1 = (time.time() - start) * 1000
print(f"First call: {elapsed1:.0f}ms (cached: {result1.cached})")

# Second call - cache hit
start = time.time()
result2 = await flow.analyze_document(
    document_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    analysis_type="comprehensive"
)
elapsed2 = (time.time() - start) * 1000
print(f"Second call: {elapsed2:.0f}ms (cached: {result2.cached})")

print(f"Speedup: {elapsed1/elapsed2:.1f}x faster")
```

**Output Example:**
```
First call: 4523ms (cached: False)
Second call: 12ms (cached: True)
Speedup: 376.9x faster
```

---

## Error Handling

### Graceful Degradation

```python
try:
    result = await flow.analyze_document(
        document_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        analysis_type="comprehensive"
    )

    # Check for partial failures
    if result.metrics.total_failed > 0:
        print(f"Warning: {result.metrics.total_failed} ratios could not be calculated")
        print(f"Quality Score: {result.quality_score}%")

    # Check if micro-agents failed
    if result.insights.risk_assessment == "insufficient_data":
        print("Warning: AI insights unavailable - using calculated ratios only")

except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Analysis failed: {e}")
    # Fallback to basic analysis
```

---

## Complete Workflow Example

### End-to-End Financial Analysis Pipeline

```python
async def analyze_financial_case(case_id: UUID, document_ids: List[UUID]):
    """Complete financial analysis workflow"""

    # Step 1: Analyze each document
    print("Step 1: Analyzing documents...")
    analyses = []
    for doc_id in document_ids:
        result = await flow.analyze_document(
            document_id=doc_id,
            analysis_type="comprehensive"
        )
        analyses.append(result)
        print(f"  ✓ Document {doc_id}: Quality {result.quality_score}%")

    # Step 2: Query for specific insights
    print("\nStep 2: Cross-document queries...")
    queries = [
        "What is the debt-to-equity ratio?",
        "What are the revenue trends?",
        "Are there any liquidity concerns?"
    ]

    for query in queries:
        results = await flow.query_case(case_id, query, context_window=1)
        print(f"  {query}")
        print(f"    Found {len(results)} relevant passages")

    # Step 3: Aggregate insights
    print("\nStep 3: Aggregating insights...")
    all_concerns = []
    all_strengths = []

    for analysis in analyses:
        all_concerns.extend(analysis.insights.key_concerns)
        all_strengths.extend(analysis.insights.key_strengths)

    # Step 4: Summary report
    print("\n" + "="*60)
    print("FINANCIAL ANALYSIS SUMMARY")
    print("="*60)
    print(f"Documents Analyzed: {len(analyses)}")
    print(f"Average Quality Score: {sum(a.quality_score for a in analyses)/len(analyses):.1f}%")
    print(f"Total Ratios Calculated: {sum(a.metrics.total_calculated for a in analyses)}")

    print(f"\nAggregated Concerns ({len(set(all_concerns))} unique):")
    for concern in set(all_concerns):
        print(f"  ⚠️  {concern}")

    print(f"\nAggregated Strengths ({len(set(all_strengths))} unique):")
    for strength in set(all_strengths):
        print(f"  ✅ {strength}")

# Run analysis
await analyze_financial_case(
    case_id=UUID("abc12345-def6-7890-ghij-klmnopqrstuv"),
    document_ids=[
        UUID("123e4567-e89b-12d3-a456-426614174000"),
        UUID("234f5678-f90c-23e4-b567-537725185001")
    ]
)
```

---

## Performance Considerations

1. **Caching**: Results cached for 1 hour (3600s) - adjust `CACHE_TTL_SECONDS` if needed
2. **Analysis Types**: Use specific types ("liquidity", "quick") for faster analysis
3. **Context Window**: Larger windows (>2) increase search time
4. **Batch Processing**: Analyze multiple documents in parallel with `asyncio.gather()`

```python
# Parallel analysis
import asyncio

results = await asyncio.gather(*[
    flow.analyze_document(doc_id, "quick")
    for doc_id in document_ids
])
```
