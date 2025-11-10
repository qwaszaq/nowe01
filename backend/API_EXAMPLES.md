# Document Management API - Example Usage

## Overview

REST API for document upload, processing, and management. Documents are processed asynchronously in the background with real-time status tracking.

**Base URL:** `http://localhost:8000/api/v1`

---

## Authentication

Currently no authentication required (add JWT/API key in production).

---

## Endpoints

### 1. Upload Document

Upload a PDF document for processing. File is validated, saved, and processing starts immediately in background.

**Endpoint:** `POST /api/v1/documents/upload`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "case_id=550e8400-e29b-41d4-a716-446655440001" \
  -F "file=@/path/to/financial_report.pdf"
```

**Response (201 Created):**
```json
{
  "document_id": "750e8400-e29b-41d4-a716-446655440002",
  "status": "processing",
  "message": "Document uploaded successfully and processing started"
}
```

**Error Cases:**
- `400 Bad Request` - Invalid file type, missing parameters
- `404 Not Found` - Case not found
- `413 Payload Too Large` - File exceeds max size (500MB)
- `500 Internal Server Error` - Server error

---

### 2. List Documents

Get paginated list of documents with optional filtering.

**Endpoint:** `GET /api/v1/documents`

**Query Parameters:**
- `case_id` (UUID, optional) - Filter by case
- `status` (string, optional) - Filter by status: pending, processing, completed, failed
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 20, max: 100) - Items per page

**Examples:**

All documents:
```bash
curl "http://localhost:8000/api/v1/documents"
```

Filter by case:
```bash
curl "http://localhost:8000/api/v1/documents?case_id=550e8400-e29b-41d4-a716-446655440001"
```

Filter by status:
```bash
curl "http://localhost:8000/api/v1/documents?status=completed"
```

Pagination:
```bash
curl "http://localhost:8000/api/v1/documents?page=2&page_size=10"
```

Combined filters:
```bash
curl "http://localhost:8000/api/v1/documents?case_id=550e8400-e29b-41d4-a716-446655440001&status=completed&page=1&page_size=20"
```

**Response (200 OK):**
```json
{
  "documents": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440002",
      "case_id": "550e8400-e29b-41d4-a716-446655440001",
      "filename": "750e8400-e29b-41d4-a716-446655440002.pdf",
      "original_filename": "Q4 2023 Financial Report.pdf",
      "status": "completed",
      "file_size": 2457600,
      "mime_type": "application/pdf",
      "page_count": 45,
      "chunk_count": 128,
      "created_at": "2024-01-15T10:30:00",
      "processing_started_at": "2024-01-15T10:30:05",
      "processing_completed_at": "2024-01-15T10:32:15"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

### 3. Get Document Details

Retrieve detailed information about a specific document.

**Endpoint:** `GET /api/v1/documents/{document_id}`

**Example:**
```bash
curl "http://localhost:8000/api/v1/documents/750e8400-e29b-41d4-a716-446655440002"
```

**Response (200 OK):**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "case_id": "550e8400-e29b-41d4-a716-446655440001",
  "filename": "750e8400-e29b-41d4-a716-446655440002.pdf",
  "original_filename": "Q4 2023 Financial Report.pdf",
  "status": "completed",
  "file_size": 2457600,
  "mime_type": "application/pdf",
  "page_count": 45,
  "chunk_count": 128,
  "created_at": "2024-01-15T10:30:00",
  "processing_started_at": "2024-01-15T10:30:05",
  "processing_completed_at": "2024-01-15T10:32:15"
}
```

**Error Cases:**
- `404 Not Found` - Document not found

---

### 4. Get Processing Status (Real-time)

Get current processing status with progress tracking. Useful for monitoring long-running operations.

**Endpoint:** `GET /api/v1/documents/{document_id}/status`

**Example:**
```bash
curl "http://localhost:8000/api/v1/documents/750e8400-e29b-41d4-a716-446655440002/status"
```

**Response (200 OK):**
```json
{
  "document_id": "750e8400-e29b-41d4-a716-446655440002",
  "state": "embedding",
  "progress_percent": 65.0,
  "current_stage": "embedding",
  "error_details": null,
  "started_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:31:30"
}
```

**Processing States:**
- `pending` - Waiting to start
- `extracting` - Extracting text from PDF
- `chunking` - Splitting text into chunks
- `embedding` - Generating embeddings
- `storing` - Storing in vector database
- `completed` - Processing finished successfully
- `failed` - Processing failed (see error_details)

**Error Cases:**
- `404 Not Found` - Document not found

---

### 5. Delete Document

Delete document and all associated data (file, embeddings, database records).

**Endpoint:** `DELETE /api/v1/documents/{document_id}`

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/750e8400-e29b-41d4-a716-446655440002"
```

**Response (204 No Content):**
```
(empty response)
```

**Error Cases:**
- `404 Not Found` - Document not found
- `500 Internal Server Error` - Deletion failed

---

### 6. Reprocess Failed Document

Retry processing a document that failed. Only works for documents with status "failed".

**Endpoint:** `POST /api/v1/documents/{document_id}/reprocess`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/750e8400-e29b-41d4-a716-446655440002/reprocess"
```

**Response (200 OK):**
```json
{
  "document_id": "750e8400-e29b-41d4-a716-446655440002",
  "status": "processing",
  "message": "Document queued for reprocessing"
}
```

**Error Cases:**
- `404 Not Found` - Document not found
- `400 Bad Request` - Document not in failed state or file missing

---

## Complete Workflow Example

### Step 1: Create a case (if not exists)
```bash
# First ensure you have a case
CASE_ID="550e8400-e29b-41d4-a716-446655440001"
```

### Step 2: Upload document
```bash
RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "case_id=${CASE_ID}" \
  -F "file=@./financial_report_q4_2023.pdf" \
  -s)

DOCUMENT_ID=$(echo $RESPONSE | jq -r '.document_id')
echo "Document uploaded: $DOCUMENT_ID"
```

### Step 3: Monitor processing status
```bash
# Poll status every 2 seconds
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/v1/documents/${DOCUMENT_ID}/status")
  STATE=$(echo $STATUS | jq -r '.state')
  PROGRESS=$(echo $STATUS | jq -r '.progress_percent')

  echo "State: $STATE, Progress: $PROGRESS%"

  if [ "$STATE" = "completed" ] || [ "$STATE" = "failed" ]; then
    break
  fi

  sleep 2
done
```

### Step 4: Get document details
```bash
curl "http://localhost:8000/api/v1/documents/${DOCUMENT_ID}" | jq
```

### Step 5: List all documents for case
```bash
curl "http://localhost:8000/api/v1/documents?case_id=${CASE_ID}" | jq
```

---

## Testing with Python

```python
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
CASE_ID = "550e8400-e29b-41d4-a716-446655440001"

# Upload document
with open("financial_report.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        data={"case_id": CASE_ID},
        files={"file": ("report.pdf", f, "application/pdf")}
    )

document_id = response.json()["document_id"]
print(f"Uploaded: {document_id}")

# Monitor status
import time
while True:
    status = requests.get(f"{BASE_URL}/documents/{document_id}/status").json()
    print(f"State: {status['state']}, Progress: {status['progress_percent']}%")

    if status['state'] in ['completed', 'failed']:
        break

    time.sleep(2)

# Get document details
document = requests.get(f"{BASE_URL}/documents/{document_id}").json()
print(f"Chunks: {document['chunk_count']}, Pages: {document['page_count']}")
```

---

## Health Check

Check API health:
```bash
curl "http://localhost:8000/api/v1/documents/health"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "document_api",
  "dependencies": {
    "postgres": {
      "status": "healthy",
      "database": "investigation_db",
      "host": "localhost"
    },
    "upload_directory": {
      "exists": true,
      "writable": true,
      "path": "./data/uploads"
    }
  }
}
```

---

## Interactive API Documentation

Once the server is running, visit:

- **Swagger UI:** http://localhost:8000/api/v1/docs
- **ReDoc:** http://localhost:8000/api/v1/redoc

These provide interactive API testing interfaces.

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "document_id": "optional-document-id"
}
```

Common HTTP status codes:
- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success with no response body
- `400 Bad Request` - Invalid request
- `404 Not Found` - Resource not found
- `413 Payload Too Large` - File too large
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Production Considerations

1. **Authentication:** Add JWT or API key authentication
2. **Rate Limiting:** Implement rate limiting for upload endpoint
3. **File Scanning:** Add virus/malware scanning before processing
4. **Storage:** Use S3/cloud storage instead of local disk
5. **Webhooks:** Add webhook notifications for processing completion
6. **Monitoring:** Integrate with Prometheus/Grafana
7. **Logging:** Use structured logging (JSON) for better analysis
