# Financial Analysis API - Example Usage

This document provides comprehensive examples for using the Financial Analysis REST API endpoints.

## Base URL
```
http://localhost:8000/api/v1
```

## Available Endpoints

### 1. POST /api/analysis/analyze
Run financial analysis on a document

### 2. GET /api/analysis/{document_id}
Get cached analysis results

### 3. POST /api/analysis/search
Semantic search across case or document

### 4. GET /api/analysis/{document_id}/metrics
Get specific metrics for document

### 5. GET /api/analysis/{document_id}/insights
Get AI insights only

### 6. GET /api/analysis/health
Health check

---

## Example 1: Comprehensive Analysis

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/api/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "analysis_type": "comprehensive"
  }'
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "analysis_type": "comprehensive",
  "quality_score": 87.5,
  "metrics": [
    {
      "metric_name": "current_ratio",
      "metric_value": 2.15,
      "metric_unit": "ratio",
      "interpretation": "Strong liquidity - company can cover short-term obligations 2.15x",
      "category": "liquidity",
      "citations": [
        {
          "page_numbers": [5],
          "formula": "Current Assets / Current Liabilities"
        }
      ]
    },
    {
      "metric_name": "roe",
      "metric_value": 18.5,
      "metric_unit": "percent",
      "interpretation": "Above-average return on equity",
      "category": "profitability",
      "citations": [
        {
          "page_numbers": [6],
          "formula": "Net Income / Shareholders' Equity"
        }
      ]
    },
    {
      "metric_name": "debt_to_equity",
      "metric_value": 0.65,
      "metric_unit": "ratio",
      "interpretation": "Moderate leverage - conservative capital structure",
      "category": "leverage",
      "citations": [
        {
          "page_numbers": [7],
          "formula": "Total Debt / Total Equity"
        }
      ]
    }
  ],
  "insights": {
    "risk_assessment": "low",
    "liquidity_position": "strong",
    "profitability_trends": "stable",
    "leverage_analysis": "moderate",
    "overall_health": "good",
    "key_concerns": [
      "Operating margin slightly below industry average"
    ],
    "key_strengths": [
      "Strong liquidity position (current ratio > 2.0)",
      "Conservative leverage (D/E < 0.5)",
      "Excellent debt service capacity (coverage > 8x)"
    ],
    "classification_count": 3
  },
  "cached": false,
  "execution_time_ms": 2543.75,
  "timestamp": "2025-11-10T15:30:00Z"
}
```

---

## Example 2: Liquidity Analysis Only

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/api/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "analysis_type": "liquidity"
  }'
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "analysis_type": "liquidity",
  "quality_score": 92.0,
  "metrics": [
    {
      "metric_name": "current_ratio",
      "metric_value": 2.15,
      "metric_unit": "ratio",
      "interpretation": "Strong liquidity",
      "category": "liquidity",
      "citations": []
    },
    {
      "metric_name": "quick_ratio",
      "metric_value": 1.78,
      "metric_unit": "ratio",
      "interpretation": "Solid quick assets coverage",
      "category": "liquidity",
      "citations": []
    },
    {
      "metric_name": "cash_ratio",
      "metric_value": 0.65,
      "metric_unit": "ratio",
      "interpretation": "Healthy cash reserves",
      "category": "liquidity",
      "citations": []
    }
  ],
  "insights": {
    "risk_assessment": "insufficient_data",
    "liquidity_position": "insufficient_data",
    "profitability_trends": "insufficient_data",
    "leverage_analysis": "insufficient_data",
    "overall_health": "insufficient_data",
    "key_concerns": [],
    "key_strengths": [],
    "classification_count": 0
  },
  "cached": false,
  "execution_time_ms": 1245.50,
  "timestamp": "2025-11-10T15:35:00Z"
}
```

---

## Example 3: Quick Analysis (Key Ratios)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/api/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "analysis_type": "quick"
  }'
```

**Analysis Types:**
- **comprehensive**: All 19 ratios + AI insights
- **liquidity**: 5 liquidity ratios (current, quick, cash, operating CF, defensive interval)
- **profitability**: 8 profitability ratios (gross margin, operating margin, net margin, ROA, ROE, ROIC, EPS, asset turnover)
- **leverage**: 6 leverage ratios (debt-to-equity, debt-to-assets, interest coverage, debt service coverage, equity multiplier, financial leverage)
- **quick**: 3 key ratios (current ratio, ROE, debt-to-equity)

---

## Example 4: Get Cached Analysis Results

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/api/analysis/550e8400-e29b-41d4-a716-446655440000?analysis_type=comprehensive"
```

**Response (Cached):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "analysis_type": "comprehensive",
  "quality_score": 87.5,
  "metrics": [...],
  "insights": {...},
  "cached": true,
  "execution_time_ms": 12.34,
  "timestamp": "2025-11-10T15:30:00Z"
}
```

**Response (Not Cached - 404):**
```json
{
  "detail": "No cached analysis found for document 550e8400-e29b-41d4-a716-446655440000 with type comprehensive. Use POST /analyze to generate."
}
```

---

## Example 5: Semantic Search (Case-wide)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/api/analysis/search \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "660e8400-e29b-41d4-a716-446655440000",
    "query": "What is the company revenue growth rate?",
    "limit": 10,
    "context_window": 1
  }'
```

**Response:**
```json
[
  {
    "chunk_id": "doc123_chunk_45",
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "page_num": 5,
    "text": "Total revenue for FY2024 was $2.5M, representing 15% growth compared to FY2023...",
    "score": 0.92,
    "context": {
      "before": [
        {
          "text": "The company experienced strong market demand throughout the fiscal year."
        }
      ],
      "after": [
        {
          "text": "Operating expenses increased by 8% due to expansion initiatives."
        }
      ]
    }
  },
  {
    "chunk_id": "doc123_chunk_67",
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "page_num": 12,
    "text": "Revenue growth accelerated in Q4, driven by new product launches...",
    "score": 0.85,
    "context": null
  }
]
```

---

## Example 6: Get Specific Metrics

**Request (All Metrics):**
```bash
curl -X GET "http://localhost:8000/api/v1/api/analysis/550e8400-e29b-41d4-a716-446655440000/metrics"
```

**Request (Filtered Metrics):**
```bash
curl -X GET "http://localhost:8000/api/v1/api/analysis/550e8400-e29b-41d4-a716-446655440000/metrics?metric_names=current_ratio,roe,debt_to_equity"
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "metrics": [
    {
      "metric_name": "current_ratio",
      "metric_value": 2.15,
      "metric_unit": "ratio",
      "interpretation": "Stored metric value",
      "category": "liquidity",
      "citations": [
        {
          "page_number": 5,
          "calculation_method": "Current Assets / Current Liabilities"
        }
      ]
    },
    {
      "metric_name": "roe",
      "metric_value": 18.5,
      "metric_unit": "percent",
      "interpretation": "Stored metric value",
      "category": "profitability",
      "citations": [
        {
          "page_number": 6,
          "calculation_method": "Net Income / Shareholders' Equity"
        }
      ]
    },
    {
      "metric_name": "debt_to_equity",
      "metric_value": 0.65,
      "metric_unit": "ratio",
      "interpretation": "Stored metric value",
      "category": "leverage",
      "citations": [
        {
          "page_number": 7,
          "calculation_method": "Total Debt / Total Equity"
        }
      ]
    }
  ],
  "total_count": 3,
  "timestamp": "2025-11-10T15:40:00Z"
}
```

---

## Example 7: Get AI Insights Only

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/api/analysis/550e8400-e29b-41d4-a716-446655440000/insights"
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "insights": {
    "risk_assessment": "low",
    "liquidity_position": "strong",
    "profitability_trends": "stable",
    "leverage_analysis": "moderate",
    "overall_health": "good",
    "key_concerns": [
      "Operating margin slightly below industry average",
      "Inventory turnover could be improved"
    ],
    "key_strengths": [
      "Strong liquidity position (current ratio > 2.0)",
      "Conservative leverage (D/E < 0.5)",
      "Excellent debt service capacity (coverage > 8x)",
      "Outstanding ROE (> 20%)"
    ],
    "classification_count": 3
  },
  "timestamp": "2025-11-10T15:45:00Z"
}
```

---

## Example 8: Health Check

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/api/analysis/health"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "analysis_api",
  "initialized": true,
  "timestamp": "2025-11-10T15:50:00.123456"
}
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Document 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid analysis_type: invalid. Must be one of: ['comprehensive', 'liquidity', 'profitability', 'leverage', 'quick']"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Analysis failed: Connection timeout"
}
```

---

## Integration Example (Python)

```python
import requests
import json
from uuid import UUID

BASE_URL = "http://localhost:8000/api/v1/api/analysis"

# 1. Run comprehensive analysis
def analyze_document(document_id: UUID, analysis_type: str = "comprehensive"):
    response = requests.post(
        f"{BASE_URL}/analyze",
        json={
            "document_id": str(document_id),
            "analysis_type": analysis_type
        }
    )
    response.raise_for_status()
    return response.json()

# 2. Get cached results
def get_cached_analysis(document_id: UUID, analysis_type: str = "comprehensive"):
    response = requests.get(
        f"{BASE_URL}/{document_id}",
        params={"analysis_type": analysis_type}
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()

# 3. Search documents
def search_case(case_id: UUID, query: str, limit: int = 10):
    response = requests.post(
        f"{BASE_URL}/search",
        json={
            "case_id": str(case_id),
            "query": query,
            "limit": limit,
            "context_window": 1
        }
    )
    response.raise_for_status()
    return response.json()

# 4. Get specific metrics
def get_metrics(document_id: UUID, metric_names: list = None):
    params = {}
    if metric_names:
        params["metric_names"] = ",".join(metric_names)

    response = requests.get(
        f"{BASE_URL}/{document_id}/metrics",
        params=params
    )
    response.raise_for_status()
    return response.json()

# 5. Get insights
def get_insights(document_id: UUID):
    response = requests.get(f"{BASE_URL}/{document_id}/insights")
    response.raise_for_status()
    return response.json()

# Example usage
if __name__ == "__main__":
    doc_id = UUID("550e8400-e29b-41d4-a716-446655440000")

    # Perform analysis
    print("Running comprehensive analysis...")
    result = analyze_document(doc_id, "comprehensive")
    print(f"Quality Score: {result['quality_score']}%")
    print(f"Metrics Calculated: {len(result['metrics'])}")
    print(f"Cached: {result['cached']}")
    print(f"Execution Time: {result['execution_time_ms']:.0f}ms")

    # Get cached results (should be instant)
    print("\nRetrieving cached results...")
    cached = get_cached_analysis(doc_id)
    if cached:
        print(f"Cached result retrieved in {cached['execution_time_ms']:.0f}ms")

    # Get specific metrics
    print("\nRetrieving specific metrics...")
    metrics = get_metrics(doc_id, ["current_ratio", "roe", "debt_to_equity"])
    for metric in metrics["metrics"]:
        print(f"{metric['metric_name']}: {metric['metric_value']}")

    # Get insights
    print("\nRetrieving insights...")
    insights = get_insights(doc_id)
    print(f"Overall Health: {insights['insights']['overall_health']}")
    print(f"Risk Assessment: {insights['insights']['risk_assessment']}")
```

---

## Caching Behavior

- Analysis results are **automatically cached** for **1 hour** (3600 seconds)
- Cache key format: `analysis:{document_id}:{analysis_type}`
- Cached results return `"cached": true` and have sub-millisecond response times
- Cache is stored in Redis for high performance
- Different analysis types have separate cache entries

---

## Performance Benchmarks

| Analysis Type   | Typical Execution Time | Metrics Calculated |
|----------------|------------------------|-------------------|
| comprehensive  | 2-5 seconds           | 19 ratios         |
| liquidity      | 1-2 seconds           | 5 ratios          |
| profitability  | 1-2 seconds           | 8 ratios          |
| leverage       | 1-2 seconds           | 6 ratios          |
| quick          | < 1 second            | 3 ratios          |
| cached (any)   | < 50ms                | N/A               |

---

## Next Steps

1. **Initialize dependencies** in your FastAPI app startup
2. **Call** `set_dependencies(analysis_flow, postgres_store)` after creating instances
3. **Test endpoints** using the curl commands above
4. **Monitor** cache hit rates via Redis
5. **Optimize** by running quick analysis first, then comprehensive if needed
