# 🚀 Datly — Talk to Your Data

> **An AI-powered Conversational Business Intelligence platform that lets you query, analyze, visualize, and understand your data using natural language.**

Datly is a high-performance **Conversational BI engine** that allows users to upload multiple **CSV and Excel datasets** and interact with their data using plain English.

Instead of manually writing SQL queries, users can simply ask questions such as:

* *"What are the top 10 products by sales?"*
* *"Show me the monthly revenue trend."*
* *"Find unusual transactions in the dataset."*
* *"Now filter the results to Chicago."*

Datly uses **LLMs, LangGraph, DuckDB, and FastAPI** to understand the user's intent, discover the relevant schema, generate safe SQL, execute analytical queries, detect anomalies, recommend visualizations, and generate meaningful insights.


<p align="center">
  <img src="https://img.shields.io/badge/React-Vite-blue" />
  <img src="https://img.shields.io/badge/FastAPI-Python-green" />
  <img src="https://img.shields.io/badge/DuckDB-Analytics-yellow" />
  <img src="https://img.shields.io/badge/LangGraph-Agentic_AI-purple" />
  <img src="https://img.shields.io/badge/Ollama-Local_LLM-black" />
  <img src="https://img.shields.io/badge/Groq-Cloud_LLM-orange" />
</p>

---
## 📸 Screenshots

### 🔐 Authentication
![Datly Authentication](docs/Screenshots/img_1.png)

### 💬 Conversational AI
![Datly Chat](docs/Screenshots/img_2.png)

### 📊 Data Visualization
![Datly Visualization](docs/Screenshots/img_4.png)

### 📁 Data Querying
![Datly Datasets](docs/Screenshots/img_5.png)

### 🧠 Insights
![Datly Schema](docs/screenshots/img_3.png)

### 🔍 Data Quality & Anomaly Detection
![Datly Data Quality](docs/Screenshots/img_6.png)

### ⚡ Dashboard Generation
![Datly Insights](docs/Screenshots/img_7.png)


## ✨ Features

### 🤖 AI-Powered Data Analysis

* Ask questions about your data using natural language.
* Automatically converts natural language into DuckDB SQL.
* Supports conversational follow-up questions.
* Uses LangGraph for agent-based query orchestration.
* Supports both local and cloud LLM inference.

### 📊 Interactive Data Visualization

* Automatically recommends suitable charts.
* Supports:

  * Bar Charts
  * Line Charts
  * Pie Charts
  * Scatter Plots
* Dynamically select X and Y axes.
* Interactive visualizations powered by Recharts.

### 🔍 Data Quality & Anomaly Detection

* Automatic data quality profiling.
* Detects missing values and duplicate records.
* Calculates duplicate rates and null statistics.
* Detects anomalies using:

  * IQR
  * Z-Score
* Provides explanations for flagged outliers.

### 🛡️ Secure SQL Execution

* Validates generated SQL before execution.
* Allows only read-only analytical queries.
* Blocks dangerous DDL and DML operations.
* Uses SQL parsing to prevent unsafe database operations.
* Self-healing SQL generation automatically retries failed queries.

### ⚡ Performance & Caching

* SHA-256 based query caching.
* Cached queries return results instantly.
* Cache automatically invalidates when datasets change.
* Optimized analytical queries using DuckDB.

### 📁 Multi-File Data Ingestion

* Upload multiple CSV and Excel files.
* Automatically cleans and normalizes column names.
* Dynamically creates DuckDB tables.
* Select which datasets should be included in each query.

### 🧠 Smart Schema Understanding

* Automatic schema discovery.
* Displays active database tables and columns.
* Supports semantic column synonyms.

For example:

```text
User: "Show total cost by buyer"

cost  → amount
buyer → customer
```

This helps the LLM map natural language terms to actual database columns.

### 🔐 Authentication & Data Isolation

* Secure authentication using Clerk.
* User-specific data isolation.
* Uploaded datasets and sessions are scoped to authenticated users.
* Query cache is isolated by user.

### 🔄 Flexible LLM Routing

Choose between:

* **Ollama** — Local LLM inference
* **Groq** — Fast cloud-based LLM inference

The model backend can be switched directly from the application interface.

---

## 🏗️ System Architecture

```mermaid
graph TD
    User([User Browser]) -->|Natural Language Query| Frontend[React + Vite]
    Frontend -->|API Request| Gateway[FastAPI Backend]

    Gateway -->|Verify Identity| Clerk[Clerk Authentication]
    Gateway -->|Session & Cache| PostgreSQL[(PostgreSQL)]
    Gateway -->|Data Ingestion & Analytics| DuckDB[(DuckDB)]

    Gateway --> Controller[LangGraph Agent Controller]

    Controller --> Schema[Schema Discovery]
    Controller --> LLM[LLM Service]

    LLM --> Ollama[Ollama]
    LLM --> Groq[Groq Cloud]

    Controller --> SQL[SQL Generation]
    SQL --> Guard[Safe SQL Guard]
    Guard --> DuckDB

    DuckDB --> Anomaly[Anomaly Detection]
    DuckDB --> Charts[Chart Recommendation]
    DuckDB --> Insights[Insight Generation]

    Anomaly --> Response[Final Response]
    Charts --> Response
    Insights --> Response

    Response --> Frontend
```

---

## 🔄 Query Processing Workflow

```text
User Question
      │
      ▼
Schema Discovery
      │
      ▼
Column Synonym Matching
      │
      ▼
LLM SQL Generation
      │
      ▼
Safe SQL Validation
      │
      ▼
DuckDB Query Execution
      │
      ├───────────────┐
      ▼               ▼
Anomaly Detection   Query Results
      │               │
      └───────┬───────┘
              ▼
     Chart Recommendation
              │
              ▼
       Insight Generation
              │
              ▼
        Final Response
```

---

## 🛠️ Tech Stack

| Layer               | Technology      |
| ------------------- | --------------- |
| Frontend            | React, Vite     |
| UI & Charts         | Recharts        |
| Backend             | FastAPI, Python |
| Agent Framework     | LangGraph       |
| Analytics Engine    | DuckDB          |
| Persistent Database | PostgreSQL      |
| Fallback Database   | SQLite          |
| Local LLM           | Ollama          |
| Cloud LLM           | Groq            |
| Authentication      | Clerk           |
| SQL Validation      | sqlparse        |
| Data Processing     | Python, Pandas  |

---

## 📂 Project Structure

```text
Datly/
│
├── backend/
│   ├── api_server.py
│   ├── database/
│   ├── models/
│   ├── services/
│   ├── agents/
│   ├── tools/
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites

Make sure you have the following installed:

* Python 3.10+
* Node.js 18+
* PostgreSQL
* Ollama

Install and run Ollama, then pull the default model:

```bash
ollama pull llama3.1
```

---

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/datly.git
cd datly
```

---

### 3. Configure Backend

Navigate to the backend:

```bash
cd backend
```

Create a `.env` file:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/analytics_gpt

DUCKDB_PATH=database/analytics_duck.db

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

GROQ_API_KEY=YOUR_API_KEY_HERE

LOG_LEVEL=INFO
```

---

### 4. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Initialize Database

```bash
python -c "from database.pg_db import get_engine; from models.pg_models import Base; Base.metadata.create_all(bind=get_engine())"
```

---

### 6. Start FastAPI Backend

```bash
python -m uvicorn api_server:app --reload --port 8000
```

The backend will be available at:

```text
http://localhost:8000
```

---

### 7. Start Frontend

Open a new terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

Open the application:

```text
http://localhost:5173
```

---

## 💡 Example Queries

Once your dataset is uploaded, you can ask questions like:

```text
What are the top 10 products by revenue?
```

```text
Show the monthly sales trend.
```

```text
Which customers have the highest total spending?
```

```text
Find unusual transactions in the dataset.
```

```text
Show me the results as a bar chart.
```

```text
Now filter it to Chicago.
```

Datly maintains conversational context, allowing users to ask follow-up questions without repeating the original query.

---

## 🧠 Self-Healing SQL

Datly includes an automatic SQL correction loop.

```text
Natural Language Query
        │
        ▼
Generate SQL
        │
        ▼
Validate SQL
        │
        ▼
Execute in DuckDB
        │
        ├── Success ──► Return Results
        │
        └── Error
             │
             ▼
      Send Error to LLM
             │
             ▼
       Regenerate SQL
             │
             ▼
          Retry
```

The system can automatically analyze DuckDB execution errors and regenerate corrected SQL queries, with a limited retry mechanism to prevent infinite execution loops.

---

## 🔒 Security

Datly implements multiple security mechanisms:

* Clerk-based authentication.
* User-level data isolation.
* Read-only SQL enforcement.
* DDL/DML query blocking.
* SQL validation before execution.
* User-scoped query caching.
* Dataset-level access control.

Only analytical read operations are permitted through the natural-language query interface.

---

## ⚡ Performance

Datly is optimized for fast analytical workloads using:

* DuckDB for high-performance local analytics.
* Query result caching.
* SHA-256 cache keys.
* Efficient schema discovery.
* Local LLM execution with Ollama.
* High-speed cloud inference through Groq.
* Asynchronous model routing.

---

## 🔮 Future Enhancements

* [ ] RAG-powered business documentation analysis
* [ ] Automatic dashboard generation
* [ ] Multi-user team workspaces
* [ ] Role-based access control
* [ ] Scheduled reports
* [ ] Email/Slack report delivery
* [ ] Advanced forecasting
* [ ] Predictive analytics
* [ ] Natural language dashboard editing
* [ ] Support for SQL databases such as MySQL and PostgreSQL
* [ ] Voice-based data analysis
* [ ] AI-generated executive reports

---

## 🎯 Why Datly?

Traditional BI tools often require users to understand SQL, database schemas, or complex dashboard builders.

**Datly simplifies data analysis by allowing users to simply talk to their data.**

```text
Upload Data
     ↓
Ask a Question
     ↓
AI Understands Your Intent
     ↓
SQL Generated Automatically
     ↓
Data Analyzed
     ↓
Charts + Anomalies + Insights
```

Datly bridges the gap between **natural language and business intelligence**, making data exploration accessible to both technical and non-technical users.

---

## 👨‍💻 Author

**Monish Kanna**

Built as an AI/ML project focused on **Conversational AI, Agentic Workflows, Natural Language to SQL, Business Intelligence, and Data Analytics**.

---

## ⭐ Support

If you find this project useful, consider giving it a ⭐ on GitHub!
