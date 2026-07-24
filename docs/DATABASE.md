# Database Schemas

Datly utilizes a two-tier database model: **PostgreSQL** (or SQLite fallback) for stateful data configurations, and **DuckDB** for analytical calculations.

---

## 💾 PostgreSQL/SQLite Models

```
+------------------+         +------------------+
|      users       |         |  uploaded_files  |
|------------------|         |------------------|
| id (PK)          | <------+ | id (PK)          |
| username         |         | user_id (FK)     |
| created_at       |         | filename         |
+------------------+         | table_name       |
         |                   | row_count        |
         |                   | columns_json     |
         |                   | created_at       |
         |                   +------------------+
         |
         +----------------------------------+
         |                                  |
         v                                  v
+------------------+              +--------------------+
|  chat_sessions   |              | dashboard_widgets  |
|------------------|              |--------------------|
| id (PK)          | <----------+ | id (PK)            |
| user_id (FK)     |            | | user_id (FK)       |
| title            |            | | title              |
| created_at       |            | | widget_type        |
+------------------+            | | config_json        |
         |                      | | data_json          |
         v                      | | created_at         |
+------------------+            | +--------------------+
|  chat_messages   |            |
|------------------|            | 
| id (PK)          |            | +--------------------+
| session_id (FK)  |            | | query_result_caches|
| role             |            | |--------------------|
| text             |            | | query_hash (PK)    |
| sql_query        |            | | user_id (FK)       |
| reasoning        |            | | sql_query          |
| anomalies_json   |            | | explanation        |
| chart_info_json  |            | | reasoning          |
| data_json        |            | | anomalies_json     |
| execution_time_ms|            | | chart_info_json    |
| created_at       |            | | result_data_json   |
+------------------+            | | created_at         |
                                | +--------------------+
                                |
                                +----------------------+
```

### 1. `users` Table
* Stores Clerk user details. ID maps to Clerk `user_id` string context.

### 2. `chat_sessions` & `chat_messages` Tables
* `chat_sessions` tracks conversation threads.
* `chat_messages` logs role dialogues ('user', 'assistant') and persists JSON datasets (`data_json`) and recommended configurations (`chart_info_json`).

### 3. `uploaded_files` Table
* Retains registries for uploaded files. Indexes column structures (`columns_json`) and target filenames in DuckDB.

### 4. `dashboard_widgets` Table
* Holds generated dashboard metrics and breakdown plots (`config_json` and `data_json`).

### 5. `query_result_caches` Table
* Indexes cache items by SHA-256 hashes (`query_hash`) of query text + scopes, allowing instant loads.

---

## 🦆 DuckDB Analytics Warehouse

* **Engine**: DuckDB acts as an in-process column-oriented database for SQL computations.
* **Namespace Isolation**: Table names are formatted as:
  `u_{clerk_user_id}_{clean_file_name}`
* **AST Validation**: SQL generations undergo safety checking with `sqlparse` before execution to restrict usage to SELECT scopes.
