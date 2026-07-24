import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Cache store for database schemas to satisfy caching requirement
_schema_cache: Dict[str, Any] = {}

def get_schema(force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """
    Discovers the database schema and columns from DuckDB.
    Returns a dictionary mapping table names to their lists of column metadata.
    Implements in-memory caching to avoid repeated catalog queries.
    """
    global _schema_cache
    
    if _schema_cache and not force_refresh:
        logger.debug("Schema fetched from cache.")
        return _schema_cache

    logger.info("Discovering DuckDB database schema...")
    try:
        from database.duckdb_manager import inspect_duckdb_schema
        discovered_schema = inspect_duckdb_schema()
        _schema_cache = discovered_schema
        logger.info(f"DuckDB schema discovered successfully: {list(discovered_schema.keys())}")
        return discovered_schema
    except Exception as e:
        logger.error(f"Error during schema discovery: {str(e)}")
        return {}

def get_user_schema(user_id: str = None, selected_tables: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetches DuckDB schemas and filters them to include only tables belonging
    to the specific user_id (prefixed with u_<user_id>_), optionally filtered by selected_tables list.
    """
    full_schema = get_schema()
    if user_id is None:
        return full_schema
        
    # Sanitize user_id to match prefix used during ingestion
    safe_user_id = "".join(c for c in user_id if c.isalnum() or c == "_")
    prefix = f"u_{safe_user_id}_"
    user_schema = {}
    for table_name, cols in full_schema.items():
        if table_name.startswith(prefix):
            # Check if selected_tables is provided and filter by it
            if selected_tables is not None:
                if table_name in selected_tables:
                    user_schema[table_name] = cols
            else:
                user_schema[table_name] = cols
    return user_schema

def invalidate_schema_cache() -> None:
    """Invalidates the in-memory schema cache."""
    global _schema_cache
    _schema_cache.clear()
    logger.info("DuckDB schema cache invalidated.")

def get_schema_string(user_id: str = None, selected_tables: List[str] = None) -> str:
    """
    Generates a clear text-based representation of the DuckDB schema belonging to user_id,
    suitable for injection into LLM prompts.
    """
    schema = get_user_schema(user_id, selected_tables)
    if not schema:
        return "No uploaded tables exist in the database or none are selected. Please upload and select CSV/Excel files."
        
    schema_lines = []
    for table_name, columns in schema.items():
        schema_lines.append(f"Table: {table_name}")
        schema_lines.append("Columns:")
        for col in columns:
            pk_suffix = " (PRIMARY KEY)" if col["primary_key"] else ""
            schema_lines.append(f"  - {col['name']} {col['type']}{pk_suffix}")
        schema_lines.append("")  # Empty line separator between tables
        
    return "\n".join(schema_lines)
