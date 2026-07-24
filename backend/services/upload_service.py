import os
import re
import json
import logging
import pandas as pd
from typing import List, Dict, Any, Tuple
from database.pg_db import get_session
from models.pg_models import UploadedFile
from database.duckdb_manager import import_csv_to_duckdb, import_df_to_duckdb, drop_duckdb_table, get_duckdb_connection
from tools.schema_tool import invalidate_schema_cache

logger = logging.getLogger(__name__)

# Reserved SQL keywords to avoid naming tables after them
RESERVED_KEYWORDS = {
    "select", "table", "from", "where", "join", "group", "order", "by", 
    "index", "view", "alter", "create", "drop", "insert", "delete", "update",
    "with", "as", "into", "values", "on", "limit", "offset", "having"
}

def sanitize_table_name(filename: str) -> str:
    """
    Sanitizes file names into valid SQL table names:
    - Converts to lowercase
    - Replaces spaces, dashes, and special characters with underscores
    - Removes extension
    - Prevents table name starting with a number (prepends 't_')
    - Avoids conflict with SQL keywords
    """
    base_name = os.path.splitext(os.path.basename(filename))[0]
    
    clean_name = base_name.lower().strip()
    clean_name = re.sub(r'[^a-z0-9_]', '_', clean_name)
    clean_name = re.sub(r'_+', '_', clean_name)
    clean_name = clean_name.strip('_')
    
    if not clean_name:
        clean_name = "uploaded_table"
        
    if clean_name[0].isdigit():
        clean_name = f"t_{clean_name}"
        
    if clean_name in RESERVED_KEYWORDS:
        clean_name = f"t_{clean_name}"
        
    return clean_name

def save_uploaded_file(file_name: str, file_bytes: bytes, upload_dir: str = "uploads") -> str:
    """
    Saves raw file bytes into the uploads/ directory for audit purposes.
    Returns the absolute path to the saved file.
    """
    os.makedirs(upload_dir, exist_ok=True)
    
    name, ext = os.path.splitext(file_name)
    counter = 1
    unique_name = file_name
    while os.path.exists(os.path.join(upload_dir, unique_name)):
        unique_name = f"{name}_{counter}{ext}"
        counter += 1
        
    save_path = os.path.join(upload_dir, unique_name)
    with open(save_path, "wb") as f:
        f.write(file_bytes)
        
    logger.info(f"Saved uploaded file to {save_path}")
    return os.path.abspath(save_path)

def process_and_import_file(file_path: str, original_filename: str, user_id: str = None) -> Tuple[str, int]:
    """
    Reads CSV or Excel files from disk, cleans column names, imports the data into DuckDB,
    and logs metadata into PostgreSQL scoped to user_id (Clerk string ID).
    
    Returns:
        Tuple of (sanitized_table_name, row_count_imported)
    """
    # Prepend user prefix to the table name to prevent name clashes in global DuckDB
    user_prefix = ""
    if user_id:
        # Sanitize Clerk user ID (e.g. user_2xyz -> user_2xyz) for table names
        safe_user_id = "".join(c for c in user_id if c.isalnum() or c == "_")
        user_prefix = f"u_{safe_user_id}_"
        
    raw_sanitized = sanitize_table_name(original_filename)
    table_name = f"{user_prefix}{raw_sanitized}"
    
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    try:
        if ext == ".csv":
            try:
                df = pd.read_csv(file_path, nrows=5)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin1", nrows=5)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path, sheet_name=0, nrows=5)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
            
        if df.columns.size == 0:
            raise ValueError("Uploaded file contains no headers or columns.")

        cleaned_columns = []
        for col in df.columns:
            cleaned_col = str(col).strip().lower()
            cleaned_col = re.sub(r'[^a-z0-9_]', '_', cleaned_col)
            cleaned_col = re.sub(r'_+', '_', cleaned_col).strip('_')
            if not cleaned_col or cleaned_col[0].isdigit():
                cleaned_col = f"c_{cleaned_col or 'col'}"
            base_col = cleaned_col
            idx = 1
            while cleaned_col in cleaned_columns:
                cleaned_col = f"{base_col}_{idx}"
                idx += 1
            cleaned_columns.append(cleaned_col)

        # Import full data
        row_count = 0
        if ext == ".csv":
            try:
                full_df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                full_df = pd.read_csv(file_path, encoding="latin1")
            full_df.columns = cleaned_columns
            row_count = import_df_to_duckdb(full_df, table_name)
            column_metadata = [{"name": col, "type": str(full_df[col].dtype)} for col in cleaned_columns]
        else:
            full_df = pd.read_excel(file_path, sheet_name=0)
            full_df.columns = cleaned_columns
            row_count = import_df_to_duckdb(full_df, table_name)
            column_metadata = [{"name": col, "type": str(full_df[col].dtype)} for col in cleaned_columns]

        # Log metadata in PostgreSQL
        session_gen = get_session()
        session = next(session_gen)
        try:
            # Delete existing metadata for this table name if it exists (re-upload)
            existing = session.query(UploadedFile).filter_by(table_name=table_name, user_id=user_id).first()
            if existing:
                session.delete(existing)
                session.flush()

            new_file = UploadedFile(
                user_id=user_id,
                filename=original_filename,
                table_name=table_name,
                file_path=file_path,
                row_count=row_count,
                columns=column_metadata
            )
            session.add(new_file)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"PostgreSQL logging failed: {str(e)}")
            raise e
        finally:
            session.close()

        invalidate_schema_cache()
        return table_name, row_count
        
    except Exception as e:
        logger.error(f"Error importing file {file_path}: {str(e)}")
        raise e

def list_user_tables(user_id: str = None) -> List[Dict[str, Any]]:
    """Lists all user uploaded tables from PostgreSQL filtered by user_id."""
    session_gen = get_session()
    session = next(session_gen)
    try:
        query = session.query(UploadedFile)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        files = query.order_by(UploadedFile.created_at.desc()).all()
        return [f.to_dict() for f in files]
    finally:
        session.close()

def delete_user_table(table_name: str, user_id: str = None) -> None:
    """Drops a user table from DuckDB and removes its metadata from PostgreSQL if owned by user."""
    if not table_name:
        raise ValueError("Table name is required.")

    # Remove from PostgreSQL metadata
    session_gen = get_session()
    session = next(session_gen)
    try:
        query = session.query(UploadedFile).filter_by(table_name=table_name)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        file_record = query.first()
        if not file_record:
            raise ValueError(f"Table '{table_name}' does not exist or you do not have permission to delete it.")
        
        session.delete(file_record)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete metadata from PostgreSQL: {str(e)}")
        raise e
    finally:
        session.close()

    # Drop table in DuckDB
    drop_duckdb_table(table_name)
    invalidate_schema_cache()
    logger.info(f"Dropped table '{table_name}' from DuckDB and metadata.")
