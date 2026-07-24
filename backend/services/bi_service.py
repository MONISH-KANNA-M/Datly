import logging
import uuid
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from database.duckdb_manager import execute_duckdb_query
from database.pg_db import get_session
from models.pg_models import UploadedFile, DashboardWidget, User

logger = logging.getLogger(__name__)

def profile_table_quality(user_id: str, table_name: str) -> Dict[str, Any]:
    """
    Runs DuckDB analytical queries to profile dataset quality.
    Inspects null counts, uniqueness, duplicates, and ranges.
    Returns a comprehensive quality report card.
    """
    logger.info(f"Profiling dataset quality for table: {table_name}")
    
    # 1. Verify table belongs to user (user-isolation check)
    session_gen = get_session()
    db = next(session_gen)
    try:
        file_meta = db.query(UploadedFile).filter_by(table_name=table_name, user_id=user_id).first()
        if not file_meta:
            raise ValueError(f"Table '{table_name}' does not exist or permission denied.")
            
        columns = file_meta.columns  # list of dicts: [{'name': 'col', 'type': 'BIGINT', ...}]
    finally:
        db.close()

    try:
        # 2. Get total rows (unpack query result tuple)
        total_rows_df, _ = execute_duckdb_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
        total_rows = int(total_rows_df.iloc[0]["cnt"]) if not total_rows_df.empty else 0
        if total_rows == 0:
            return {
                "table_name": table_name,
                "total_rows": 0,
                "health_score": 100,
                "duplicate_rows": 0,
                "columns": []
            }

        # 3. Get duplicate rows count
        col_names_str = ", ".join([f'"{c["name"]}"' for c in columns])
        dup_query = f"""
            SELECT SUM(dup_count) as total_dups
            FROM (
                SELECT COUNT(*) - 1 as dup_count
                FROM {table_name}
                GROUP BY {col_names_str}
                HAVING COUNT(*) > 1
            )
        """
        dup_df, _ = execute_duckdb_query(dup_query)
        dup_rows = int(dup_df.iloc[0]["total_dups"]) if not dup_df.empty and pd.notnull(dup_df.iloc[0]["total_dups"]) else 0
        dup_percentage = (dup_rows / total_rows) * 100.0

        # 4. Profile each column
        column_reports = []
        total_nulls = 0
        
        for col in columns:
            col_name = col["name"]
            col_type = col["type"]
            
            # Fetch null count & distinct count
            stats_query = f"""
                SELECT 
                    COUNT(*) FILTER (WHERE "{col_name}" IS NULL) as null_cnt,
                    COUNT(DISTINCT "{col_name}") as distinct_cnt
                FROM {table_name}
            """
            stats_df, _ = execute_duckdb_query(stats_query)
            
            null_cnt = int(stats_df.iloc[0]["null_cnt"]) if not stats_df.empty else 0
            distinct_cnt = int(stats_df.iloc[0]["distinct_cnt"]) if not stats_df.empty else 0
            
            total_nulls += null_cnt
            null_pct = (null_cnt / total_rows) * 100.0
            distinct_pct = (distinct_cnt / total_rows) * 100.0
            
            # Status check
            status = "Healthy"
            if null_pct > 15.0:
                status = "High Null Rate"
            elif distinct_cnt == 1 and total_rows > 1:
                status = "Constant Value"
                
            column_reports.append({
                "name": col_name,
                "type": col_type,
                "null_count": null_cnt,
                "null_percentage": round(null_pct, 2),
                "distinct_count": distinct_cnt,
                "distinct_percentage": round(distinct_pct, 2),
                "status": status
            })

        # Calculate overall health score
        total_cells = total_rows * len(columns)
        bad_cells = total_nulls + dup_rows
        health_score = max(0, min(100, int(100.0 * (1.0 - (bad_cells / total_cells)))))

        return {
            "table_name": table_name,
            "total_rows": total_rows,
            "duplicate_rows": dup_rows,
            "duplicate_percentage": round(dup_percentage, 2),
            "columns": column_reports,
            "health_score": health_score
        }

    except Exception as e:
        logger.error(f"Failed to profile quality for table {table_name}: {str(e)}")
        raise e

def generate_auto_dashboard(user_id: str) -> List[Dict[str, Any]]:
    """
    Auto-generates metric summaries and comparison chart widgets
    for all active uploaded tables scoped to the user, and persists
    them in PostgreSQL.
    """
    logger.info(f"Generating auto-dashboard widgets for user: {user_id}")
    
    session_gen = get_session()
    db = next(session_gen)
    try:
        # Clear previous widgets for user
        db.query(DashboardWidget).filter_by(user_id=user_id).delete()
        
        # Get active tables metadata
        files = db.query(UploadedFile).filter_by(user_id=user_id).all()
        if not files:
            db.commit()
            return []
            
        generated_widgets = []

        for f in files:
            clean_name = f.table_name.replace(f"u_{user_id.replace('[^a-zA-Z0-9_]', '')}_", "")
            friendly_name = clean_name.replace("u_", "").capitalize()
            
            # --- 1. Metric widget: Row count ---
            widget_id = str(uuid.uuid4())
            row_widget = DashboardWidget(
                id=widget_id,
                user_id=user_id,
                title=f"Total Records: {friendly_name}",
                widget_type="metric",
                config={},
                data=[{"metric_value": f.row_count, "subtitle": f"Ingested from {f.filename}"}]
            )
            db.add(row_widget)
            generated_widgets.append(row_widget)

            # --- 2. Chart widget: Summary aggregator ---
            cols = f.columns
            cat_col = None
            num_col = None
            
            for c in cols:
                ctype = c["type"].upper()
                cname = c["name"]
                if ("VARCHAR" in ctype or "CHAR" in ctype or "TEXT" in ctype) and cname != "customer_id":
                    cat_col = cname
                elif ("DOUBLE" in ctype or "FLOAT" in ctype or "INT" in ctype or "DECIMAL" in ctype) and not cname.endswith("_id"):
                    num_col = cname

            if not cat_col and len(cols) > 0:
                cat_col = cols[0]["name"]
            if not num_col and len(cols) > 1:
                num_col = cols[1]["name"] if cols[1]["name"] != cat_col else cols[0]["name"]

            if cat_col and num_col and cat_col != num_col:
                try:
                    breakdown_query = f"""
                        SELECT 
                            CAST("{cat_col}" AS VARCHAR) as x_axis_val,
                            SUM(CAST("{num_col}" AS DOUBLE)) as y_axis_val
                        FROM {f.table_name}
                        WHERE "{cat_col}" IS NOT NULL AND "{num_col}" IS NOT NULL
                        GROUP BY x_axis_val
                        ORDER BY y_axis_val DESC
                        LIMIT 8
                    """
                    chart_df, _ = execute_duckdb_query(breakdown_query)
                    
                    if not chart_df.empty:
                        chart_data = chart_df.to_dict(orient="records")
                        
                        chart_widget = DashboardWidget(
                            id=str(uuid.uuid4()),
                            user_id=user_id,
                            title=f"Distribution of {num_col.capitalize()} by {cat_col.capitalize()} ({friendly_name})",
                            widget_type="chart",
                            config={
                                "type": "bar",
                                "x_axis": "x_axis_val",
                                "y_axis": "y_axis_val"
                            },
                            data=chart_data
                        )
                        db.add(chart_widget)
                        generated_widgets.append(chart_widget)
                except Exception as e:
                    logger.warning(f"Could not build summary chart for {f.table_name}: {str(e)}")

        db.commit()
        return [w.to_dict() for w in generated_widgets]

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate dashboard widgets: {str(e)}")
        raise e
    finally:
        db.close()

def match_column_synonyms(question: str, user_schema: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    """
    Fuzzy checks user query tokens against synonyms (money -> amount, clients -> name)
    and maps them to database column keys. Returns text-based semantic hints to assist the LLM.
    """
    SYNONYMS = {
        "amount": ["price", "cost", "spent", "revenue", "sales", "money", "profits", "payment", "earnings", "total"],
        "name": ["buyer", "client", "customer", "customer_name", "user", "person"],
        "product": ["item", "goods", "commodity", "purchase", "device", "article"],
        "order_date": ["date", "time", "day", "when", "month", "year"],
        "city": ["location", "place", "state", "address", "town", "country"]
    }

    hints = []
    q_lower = question.lower()
    
    for table_name, cols in user_schema.items():
        clean_table = table_name.replace("u_user_", "")
        clean_table = clean_table.split("_")[-1] if "_" in clean_table else clean_table
        
        for col in cols:
            col_name = col["name"].lower()
            
            matched_synonym = None
            for key, syns in SYNONYMS.items():
                if col_name == key:
                    for s in syns:
                        if s in q_lower:
                            matched_synonym = s
                            break
            
            if matched_synonym:
                hints.append(
                    f"Semantic Hint: The query keyword '{matched_synonym}' corresponds directly to the column '{col['name']}' in table '{table_name}'."
                )
            elif col_name in q_lower and len(col_name) > 3:
                hints.append(
                    f"Semantic Hint: Confirmed match for column '{col['name']}' in table '{table_name}'."
                )

    return hints
