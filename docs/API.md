# API Documentation

Datly exposes a set of REST endpoints secured via Clerk authentication headers (`Authorization: Bearer <JWT>`).

---

## 🔒 Authentication
All requests must include a valid bearer token in the headers:
```http
Authorization: Bearer <clerk_session_token>
```
*The backend verifies this signature using the Clerk JWKS endpoint, falling back to local verification for offline local development.*

---

## 📂 File Registry Endpoints

### 1. Ingest Datasets (`POST /api/upload`)
* **Purpose**: Uploads and ingests one or more CSV/Excel files.
* **Payload**: Multipart Form Data with file binaries.
* **Response**:
  ```json
  {
    "files": [
      {
        "filename": "orders.csv",
        "table_name": "u_user_2xyz_orders",
        "row_count": 105,
        "success": true
      }
    ]
  }
  ```
*Invalidates query caches and dashboard widgets for the user.*

### 2. Retrieve Files (`GET /api/files`)
* **Purpose**: Lists all active tables uploaded by the user.

### 3. Delete File (`DELETE /api/files/{table_name}`)
* **Purpose**: Drops the table from DuckDB and deletes PostgreSQL metadata.
* **Response**: `{"status": "success", "message": "Table deleted."}`

---

## 💬 Chat Workspace Endpoints

### 1. Query Assistant Agent (`POST /api/chat`)
* **Purpose**: Submits a query to the conversational BI agent.
* **Payload**:
  ```json
  {
    "session_id": "a757d759-79c7-49b3-a948-22e5f80b528d",
    "question": "Show total sales by product",
    "selected_tables": ["u_user_2xyz_orders"],
    "model_provider": "auto"
  }
  ```
* **Response**:
  * Evaluates SHA-256 query cache keys.
  * If Cache Hit: Loads instantly (0ms) and returns the cached result.
  * If Cache Miss: Runs the LangGraph agent and returns findings, SQL scripts, anomalies, and chart configurations.

### 2. Create Chat Session (`POST /api/sessions`)
* **Purpose**: Initializes a new conversation thread.

### 3. Delete Session (`DELETE /api/sessions/{session_id}`)
* **Purpose**: Deletes the chat session and cascade deletes its message logs.

---

## 📈 Dashboard & Data Quality Endpoints

### 1. Generate Auto-Dashboard (`POST /api/dashboard/generate`)
* **Purpose**: Triggers DuckDB to aggregate summary cards and distribution widgets, saving them in PostgreSQL.

### 2. Fetch Dashboard (`GET /api/dashboard`)
* **Purpose**: Returns the list of dashboard metric cards and charts for the user.

### 3. Profile Table Quality (`GET /api/files/{table_name}/quality`)
* **Purpose**: Runs a real-time DuckDB check to calculate row metrics, duplicates, null counts, and column status alerts.
