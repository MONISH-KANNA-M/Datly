import pytest
import pandas as pd
import duckdb
from database.duckdb_manager import execute_duckdb_query, import_df_to_duckdb
from database.pg_db import init_pg_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Initializes the database and pre-populates dummy test tables."""
    init_pg_db()
    
    # Ingest a mock table for queries directly to DuckDB
    df = pd.DataFrame({
        "item_id": [1, 2, 3],
        "item_name": ["Widget A", "Widget B", "Widget C"],
        "price": [10.5, 20.0, 5.25]
    })
    import_df_to_duckdb(df, "sales")
    
    yield

def test_execute_select():
    # Execute valid SELECT query
    df, exec_time = execute_duckdb_query("SELECT * FROM sales")
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "item_name" in df.columns
    assert exec_time > 0.0

def test_execute_query_failure():
    # Attempt executing query on non-existing table in DuckDB
    with pytest.raises(Exception):
        execute_duckdb_query("SELECT * FROM non_existent_table")
