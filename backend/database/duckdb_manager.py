import os
import time
import logging
import duckdb
import pandas as pd
from typing import Tuple, Dict, Any, List

logger = logging.getLogger(__name__)

DEFAULT_DUCKDB_PATH = "database/analytics_duck.db"

def get_duckdb_path() -> str:
    """Retrieves and resolves the DuckDB database path from environment variables."""
    db_path = os.getenv("DUCKDB_PATH", DEFAULT_DUCKDB_PATH)
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
    
    # Ensure containing directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path

def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """Creates a new connection to the DuckDB file."""
    db_path = get_duckdb_path()
    return duckdb.connect(db_path)

def execute_duckdb_query(sql_query: str) -> Tuple[pd.DataFrame, float]:
    """
    Executes a SELECT query on DuckDB and returns the Pandas DataFrame
    along with the execution time in milliseconds.
    """
    start_time = time.perf_counter()
    conn = get_duckdb_connection()
    try:
        # Execute query and convert directly to a Pandas DataFrame
        logger.info(f"Executing query on DuckDB: {sql_query}")
        df = conn.execute(sql_query).df()
        exec_time = (time.perf_counter() - start_time) * 1000.0
        return df, exec_time
    except Exception as e:
        logger.error(f"DuckDB query execution failed: {str(e)}")
        raise e
    finally:
        conn.close()

def import_csv_to_duckdb(file_path: str, table_name: str) -> int:
    """
    Directly loads a CSV file into a DuckDB table using DuckDB's high-performance native parser.
    Returns the number of rows imported.
    """
    conn = get_duckdb_connection()
    try:
        # Use read_csv_auto for automated parsing of delimiters, headers, types
        # Note: We wrap the path in single quotes, escaping any internal quotes if necessary
        safe_path = file_path.replace("'", "''")
        query = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{safe_path}')"
        logger.info(f"Running import query: {query}")
        conn.execute(query)
        
        # Get count of imported rows
        count_res = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        row_count = count_res[0] if count_res else 0
        logger.info(f"Successfully imported {row_count} rows into DuckDB table '{table_name}'")
        return row_count
    except Exception as e:
        logger.error(f"Failed to import CSV to DuckDB: {str(e)}")
        raise e
    finally:
        conn.close()

def import_df_to_duckdb(df: pd.DataFrame, table_name: str) -> int:
    """
    Imports a Pandas DataFrame into a DuckDB table.
    Used for Excel or clean dataframes.
    """
    conn = get_duckdb_connection()
    try:
        # DuckDB can directly select from active local variables containing dataframes!
        conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
        row_count = len(df)
        logger.info(f"Successfully imported {row_count} rows from DataFrame to DuckDB table '{table_name}'")
        return row_count
    except Exception as e:
        logger.error(f"Failed to import DataFrame to DuckDB: {str(e)}")
        raise e
    finally:
        conn.close()

def drop_duckdb_table(table_name: str) -> None:
    """Drops a table from the DuckDB database."""
    conn = get_duckdb_connection()
    try:
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        logger.info(f"Dropped DuckDB table '{table_name}'")
    except Exception as e:
        logger.error(f"Failed to drop DuckDB table '{table_name}': {str(e)}")
        raise e
    finally:
        conn.close()

def inspect_duckdb_schema() -> Dict[str, List[Dict[str, Any]]]:
    """
    Inspects all tables in the DuckDB database and returns their column metadata.
    Format:
        {
            "table_name": [
                {"name": "col1", "type": "VARCHAR", "primary_key": False},
                ...
            ]
        }
    """
    conn = get_duckdb_connection()
    schema = {}
    try:
        # Query tables list
        tables_res = conn.execute("SHOW TABLES").fetchall()
        tables = [row[0] for row in tables_res]
        
        for table in tables:
            # Query column details
            cols_res = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            # cols_res columns: cid, name, type, notnull, dflt_value, pk
            columns_list = []
            for col in cols_res:
                columns_list.append({
                    "name": col[1],
                    "type": col[2],
                    "primary_key": bool(col[5])
                })
            schema[table] = columns_list
            
        return schema
    except Exception as e:
        logger.error(f"Failed to inspect DuckDB schema: {str(e)}")
        return {}
    finally:
        conn.close()
