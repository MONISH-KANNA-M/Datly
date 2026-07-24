import logging
from typing import Dict, Any
import pandas as pd
from tools.validator import validate_sql
from database.duckdb_manager import execute_duckdb_query

logger = logging.getLogger(__name__)

def run_query(sql_query: str) -> Dict[str, Any]:
    """
    Validates and runs a SQL query on the DuckDB database.
    
    Returns:
        Dict containing:
            "success": bool
            "data": pd.DataFrame (if success=True)
            "error": str (if success=False)
            "execution_time_ms": float (if success=True)
    """
    logger.info(f"Validating and executing SQL query on DuckDB: {sql_query}")
    
    # 1. Validate the SQL query first (ensure it's read-only Select/With)
    is_valid, validation_msg = validate_sql(sql_query)
    if not is_valid:
        logger.warning(f"SQL validation failed: {validation_msg}")
        return {
            "success": False,
            "data": None,
            "error": f"SQL Validation Error: {validation_msg}",
            "execution_time_ms": 0.0
        }
        
    # 2. Execute query if validation passes
    try:
        df, exec_time = execute_duckdb_query(sql_query)
        logger.info(f"DuckDB query executed successfully in {exec_time:.2f}ms. Rows returned: {len(df)}")
        return {
            "success": True,
            "data": df,
            "error": None,
            "execution_time_ms": exec_time
        }
    except Exception as e:
        logger.error(f"DuckDB execution failed: {str(e)}")
        return {
            "success": False,
            "data": None,
            "error": f"SQL Execution Error: {str(e)}",
            "execution_time_ms": 0.0
        }
