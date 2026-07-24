# Application Architecture

Datly is a Conversational Business Intelligence engine structured as a modern, decoupled single-page application and API service. It integrates local vector engines, an analytical database warehouse, and relational stores to execute secure data calculations.

---

## 🏗️ Multi-Layer Design

```
+-------------------------------------------------------------+
|                     Client Presentation                     |
|            React (Vite) / Recharts / Clerk Auth             |
+-------------------------------------------------------------+
                              |
                     HTTPS / JSON / JWT
                              v
+-------------------------------------------------------------+
|                      FastAPI Web Gateway                     |
|           Secured endpoints / SQLparse Safe Guards          |
+-------------------------------------------------------------+
         |                    |                      |
         v                    v                      v
+----------------+   +------------------+   +-----------------+
| Persistent DB  |   | Analytical DB    |   | AI Orchestrator |
| PostgreSQL /   |   | DuckDB In-Memory |   | LangGraph Node  |
| SQLite Fallback|   | SQL Compiler     |   | State Engine    |
+----------------+   +------------------+   +-----------------+
                                                     |
                                            HTTPS / JSON Payload
                                                     v
                                            +-----------------+
                                            | LLM Providers   |
                                            | Ollama / Groq   |
                                            +-----------------+
```

### 1. Presentation Layer (React client)
* **Identity Management**: Connected to **Clerk** authentication using standard popup mode modals, securing sessions on the client side.
* **Analytical Workspace**: A unified panel that handles CSV/Excel ingestion, displays database schemas, compiles interactive plots (Recharts), and renders execution times.
* **Interactive Controls**: Features a dropdown selector allowing users to route queries between local **Ollama** and cloud **Groq** servers instantly.

### 2. Service Gateway Layer (FastAPI)
* **Authentication Guards**: Resolves incoming Clerk tokens locally using a JWKS signature validator. Falls back automatically to local offline decoding to allow developer convenience.
* **SQL Injection Shield**: Uses `sqlparse` to parse generated code structures, blocking modifying operations (like `DROP`, `DELETE`, `INSERT`, `UPDATE`) from executing on files.
* **Cache Controller**: Evaluates SHA-256 hashes of queries and selected table scopes to fetch instant (0ms) repeats from the local cache.

### 3. Data Storage Layer (PostgreSQL & DuckDB)
* **Relational Database**: Persistent database storing users, messages, sessions, generated dashboard widgets, and cached query outcomes. Automatically shifts to SQLite if PostgreSQL connection fails.
* **Analytical Warehouse**: An embedded DuckDB instance that queries datasets in-memory. DuckDB handles high-speed aggregations, groupings, and data quality check profiles.

### 4. Conversational AI Agent Layer (LangGraph)
* Orchestrates analytical workflows through state-machine transitions (Schema Discovery, SQL Code Gen, Execution, Anomaly Audits, and Explanatory Syntheses).
* Details of the graph nodes can be reviewed in [docs/AGENT_FLOW.md](file:///c:/SECE/MK/NL%20to%20SQL/docs/AGENT_FLOW.md).
