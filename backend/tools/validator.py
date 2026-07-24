import logging
import sqlparse
from typing import Tuple, Set

logger = logging.getLogger(__name__)

# List of explicitly banned keywords to enforce write protection at application layer
BANNED_KEYWORDS: Set[str] = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", 
    "TRUNCATE", "ATTACH", "DETACH", "VACUUM", "PRAGMA", "REPLACE"
}

# Explicitly allowed main query keywords
ALLOWED_ROOT_KEYWORDS: Set[str] = {"SELECT", "WITH"}

def validate_sql(sql_query: str) -> Tuple[bool, str]:
    """
    Validates a SQL query using sqlparse to prevent destructive operations.
    
    Rules:
    - Must only contain SELECT or WITH queries.
    - Cannot contain any forbidden keywords (e.g., INSERT, DELETE, DROP, PRAGMA) at any level.
    
    Returns:
        Tuple[bool, str]: (is_valid, error_explanation)
    """
    if not sql_query or not sql_query.strip():
        return False, "Query is empty."

    # Strip comments first to avoid false positives on comments
    try:
        formatted_sql = sqlparse.format(sql_query, strip_comments=True).strip()
    except Exception as e:
        logger.error(f"Error parsing SQL comment stripping: {str(e)}")
        return False, f"SQL parsing error: {str(e)}"

    if not formatted_sql:
        return False, "Query contains only comments or whitespace."

    # Parse into statements
    try:
        statements = sqlparse.parse(formatted_sql)
    except Exception as e:
        logger.error(f"Error parsing SQL statement structure: {str(e)}")
        return False, f"SQL tokenization error: {str(e)}"

    for stmt in statements:
        # Check statement type
        stmt_type = stmt.get_type()
        
        # Verify the root command is SELECT or WITH
        # Note: sqlparse.parse() sometimes labels WITH queries as 'UNKNOWN', 
        # so we also check the first non-whitespace token.
        first_token = None
        for token in stmt.tokens:
            if not token.is_whitespace:
                first_token = token.value.upper()
                break
                
        if stmt_type not in ALLOWED_ROOT_KEYWORDS and first_token not in ALLOWED_ROOT_KEYWORDS:
            return False, (
                f"Query type '{stmt_type or first_token}' is blocked. "
                f"Only read-only SELECT and WITH statements are permitted."
            )
            
        # Recursively search for banned tokens
        has_banned, detail_msg = _contains_banned_tokens(stmt.tokens)
        if has_banned:
            return False, f"Security Block: {detail_msg}"
            
    return True, "Query is valid."

def _contains_banned_tokens(tokens: list) -> Tuple[bool, str]:
    """Recursively parses sqlparse tokens to locate restricted keywords."""
    for token in tokens:
        if token.is_group:
            # Recursively scan group tokens
            has_banned, msg = _contains_banned_tokens(token.tokens)
            if has_banned:
                return True, msg
        else:
            # Check keyword tokens and identifier tokens
            val = token.value.upper().strip()
            # Split tokens to check sub-words if needed
            words = val.split()
            for word in words:
                clean_word = word.strip("();,`\"'[]")
                if clean_word in BANNED_KEYWORDS:
                    return True, f"Banned instruction '{clean_word}' detected in query text."
                    
    return False, ""
