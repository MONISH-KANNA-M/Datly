# Agent Graph Workflow

Datly coordinates analytical iterations using a **StateGraph** built with **LangGraph**. The workflow discovers schemas, constructs SQL scripts, validates code syntax, executes queries against DuckDB, flags outliers, and compiles final insights.

---

## 🔁 Graph Nodes & Transitions

```
[Start]
   |
   v
(Discover Schema & Synonyms)
   |
   v
(Generate SQL Query) <-------------------------+
   |                                           |
   v                                           |
(Validate & Run Query on DuckDB)               |
   |                                           |
   +---> [If Error / Syntax Failure] ----------+ (Retries up to 3 times)
   |
   +---> [If Success]
           |
           v
     (Audit Anomalies / Outliers)
           |
           v
     (Recommend Interactive Charts)
           |
           v
     (Summarize Response & Explain)
           |
           v
         [End]
```

### 1. Discover Schema & Synonyms Node
* **Purpose**: Compiles a catalog of active table schemas selected by the user.
* **Fuzzy Synonym Mapping**: Runs token similarity checks on the user question against common terms (e.g. *cost* -> `amount`, *user* -> `name`). Appends a `=== SEMANTIC COLUMN HINTS ===` context block to guide the LLM generator.

### 2. Generate SQL Query Node
* **Purpose**: Generates read-only DuckDB SQL scripts.
* **Context Assembly**: Integrates system prompts, active schema catalogs, question histories, semantic synonym matches, and any previous runtime tracebacks if a self-healing loop was triggered.

### 3. Validate & Run Node
* **Purpose**: Runs AST check structures, blocks non-SELECT actions, and runs the script on DuckDB.
* **Self-Healing Loop**: If DuckDB throws a syntax or compile error (e.g. *column not found*), the node catches the error message and forwards it back to the SQL Generation node to rewrite and self-correct (max 3 retries).

### 4. Audit Anomalies Node
* **Purpose**: Scans query results to identify statistical outliers.
* **Methods**: Employs **IQR (Interquartile Range)** and **Z-Score** thresholds on numeric records. Flags abnormal data rows and aggregates explanations.

### 5. Recommend Charts Node
* **Purpose**: Examines schema output structures to suggest optimal visual plotting.
* **Logic**: If there is a categorical (text) column and a numeric (float) column, suggests a **Bar** or **Line** chart, and designates appropriate `x_axis` and `y_axis` targets.

### 6. Summarize & Explain Node
* **Purpose**: Synthesizes a plain-English explanation of findings and returns state outputs to the user API.
