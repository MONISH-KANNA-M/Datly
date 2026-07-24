import re
import logging
from typing import Dict, Any, Tuple
import pandas as pd

from agent.state import AgentState
from agent.retry_logic import should_retry, get_next_retry_state_updates
from agent.prompts import (
    SQL_GENERATION_SYSTEM_PROMPT, SQL_GENERATION_USER_PROMPT_TEMPLATE,
    SQL_REFINER_SYSTEM_PROMPT, SQL_REFINER_USER_PROMPT_TEMPLATE
)
from services.llm_service import generate_completion
from tools.schema_tool import get_schema_string, get_user_schema
from services.bi_service import match_column_synonyms
from tools.validator import validate_sql
from tools.sql_tool import run_query
from tools.explanation_tool import explain_results
from tools.anomaly_detector import check_for_data_anomalies
from tools.chart_recommender import recommend_chart_config

logger = logging.getLogger(__name__)

def extract_sql_from_response(text: str) -> str:
    """
    Strips LLM response markers and extracts raw SQL query text:
    - Looks for ```sql ... ```
    - Looks for general ``` ... ```
    - Trims spaces and ending semicolons
    """
    if not text:
        return ""
        
    # Match ```sql <content> ``` (case-insensitive)
    sql_match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip()
        
    # Match generic ``` <content> ```
    generic_match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if generic_match:
        return generic_match.group(1).strip()
        
    # Fallback to entire text if no markdown block found
    return text.strip()

def extract_thoughts_from_response(text: str) -> str:
    """Extracts raw reasoning text within <thoughts>...</thoughts> blocks."""
    if not text:
        return ""
    thoughts_match = re.search(r"<thoughts>\s*(.*?)\s*</thoughts>", text, re.DOTALL | re.IGNORECASE)
    if thoughts_match:
        return thoughts_match.group(1).strip()
    return "No explicit reasoning provided by the assistant."

def format_chat_history(history: list) -> str:
    """Formats chat history array into a simple text block for prompt insertion."""
    if not history:
        return "No prior history."
    formatted = []
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        text_val = msg.get("text", "")
        # Avoid putting giant data frames or code snippets in the conversational history block if possible
        text_summary = text_val[:300] + "..." if len(text_val) > 300 else text_val
        formatted.append(f"{role}: {text_summary}")
    return "\n".join(formatted)

# ==========================================
# GRAPH NODE DEFINITIONS
# ==========================================

def discover_schema_node(state: AgentState) -> Dict[str, Any]:
    """Node: Discovers and formats database schemas for context."""
    logger.info("--- NODE: Discover Schema ---")
    user_id = state.get("user_id")
    selected = state.get("selected_tables")
    
    schema_str = get_schema_string(user_id=user_id, selected_tables=selected)
    
    try:
        user_schema = get_user_schema(user_id=user_id, selected_tables=selected)
        hints = match_column_synonyms(state.get("question", ""), user_schema)
        if hints:
            hints_str = "\n".join(hints)
            schema_str = f"{schema_str}\n\n=== SEMANTIC COLUMN HINTS ===\n{hints_str}"
            logger.info(f"Appended {len(hints)} semantic synonym hints to query schema prompt context.")
    except Exception as e:
        logger.warning(f"Failed to match semantic synonyms: {str(e)}")
        
    return {
        "schema": schema_str,
        "status": "Schema discovered successfully."
    }

def generate_sql_node(state: AgentState) -> Dict[str, Any]:
    """Node: Generates SQL queries using LLM with retry/error context."""
    logger.info("--- NODE: Generate SQL ---")
    
    question = state["question"]
    schema = state["schema"]
    retry_count = state.get("retry_count", 0)
    errors = state.get("errors", [])
    last_sql = state.get("generated_sql")
    history_list = state.get("chat_history", [])
    
    history_str = format_chat_history(history_list)
    
    try:
        if retry_count == 0 or not last_sql:
            # First attempt: standard prompt
            logger.info("Attempting first-time SQL generation.")
            system_prompt = SQL_GENERATION_SYSTEM_PROMPT.format(schema=schema, chat_history=history_str)
            user_prompt = SQL_GENERATION_USER_PROMPT_TEMPLATE.format(question=question)
        else:
            # Refinement attempt: inject error from history
            logger.info(f"Attempting SQL refinement. Retry count: {retry_count}")
            last_error = errors[-1] if errors else "Unknown error"
            system_prompt = SQL_REFINER_SYSTEM_PROMPT.format(
                failed_sql=last_sql,
                error_message=last_error,
                schema=schema
            )
            user_prompt = SQL_REFINER_USER_PROMPT_TEMPLATE.format(question=question)
            
        llm_response = generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.0  # Zero temperature for precision SQL gen
        )
        
        # Check if model returned an error directly
        if llm_response.startswith("ERROR:"):
            logger.warning(f"LLM explicitly failed generation: {llm_response}")
            return {
                "errors": errors + [llm_response],
                "status": f"LLM generation error: {llm_response}"
            }
            
        sql_query = extract_sql_from_response(llm_response)
        reasoning = extract_thoughts_from_response(llm_response)
        
        logger.info(f"Extracted SQL: {sql_query}")
        
        # Keep track of SQL history
        sql_history = list(state.get("sql_history", []))
        sql_history.append(sql_query)
        
        return {
            "generated_sql": sql_query,
            "sql_history": sql_history,
            "reasoning": reasoning,
            "status": "SQL query generated."
        }
        
    except Exception as e:
        logger.error(f"Error in generate_sql_node: {str(e)}")
        return {
            "errors": errors + [f"Generation failed: {str(e)}"],
            "status": "SQL generation failed."
        }

def validate_sql_node(state: AgentState) -> Dict[str, Any]:
    """Node: Inspects query syntax and safety flags."""
    logger.info("--- NODE: Validate SQL ---")
    sql_query = state.get("generated_sql")
    
    if not sql_query:
        return {
            "success": False,
            "errors": state.get("errors", []) + ["No SQL query was generated to validate."],
            "status": "SQL validation skipped (empty query)."
        }
        
    is_valid, validation_msg = validate_sql(sql_query)
    
    if not is_valid:
        logger.warning(f"SQL Validation failed: {validation_msg}")
        # Apply retry increment
        updates = get_next_retry_state_updates(state, f"Validation failure: {validation_msg}")
        updates["status"] = f"SQL Blocked by security validator: {validation_msg}"
        return updates
        
    logger.info("SQL validation passed.")
    return {
        "success": True,
        "status": "SQL validation passed."
    }

def execute_sql_node(state: AgentState) -> Dict[str, Any]:
    """Node: Executes validated SELECT statement on DuckDB read-only connection."""
    logger.info("--- NODE: Execute SQL ---")
    sql_query = state.get("generated_sql")
    
    if not state.get("success", False) or not sql_query:
        return {
            "success": False,
            "status": "SQL execution skipped."
        }
        
    result = run_query(sql_query)
    
    if not result["success"]:
        logger.warning(f"SQL execution error: {result['error']}")
        updates = get_next_retry_state_updates(state, f"Execution failure: {result['error']}")
        updates["status"] = f"SQL Execution error: {result['error']}"
        return updates
        
    logger.info("SQL executed successfully.")
    return {
        "success": True,
        "data": result["data"],
        "status": "SQL executed successfully."
    }

def detect_anomalies_node(state: AgentState) -> Dict[str, Any]:
    """Node: Profiler to search for outliers and flag logical anomalies."""
    logger.info("--- NODE: Detect Anomalies ---")
    df = state.get("data")
    question = state["question"]
    
    if df is None or df.empty:
        return {
            "anomalies": [],
            "status": "Anomaly check skipped (empty data)."
        }
        
    anomalies = check_for_data_anomalies(question, df)
    return {
        "anomalies": anomalies,
        "status": f"Anomaly detection completed. Flagged points: {len(anomalies)}"
    }

def explain_result_node(state: AgentState) -> Dict[str, Any]:
    """Node: Requests LLM explanation for the visual query outcome."""
    logger.info("--- NODE: Explain Results ---")
    df = state.get("data")
    sql_query = state.get("generated_sql")
    question = state["question"]
    
    if df is None or not sql_query:
        return {
            "explanation": "No query data available to describe.",
            "status": "Result explanation skipped."
        }
        
    explanation = explain_results(question, sql_query, df)
    return {
        "explanation": explanation,
        "status": "Explanation generated."
    }

def recommend_chart_node(state: AgentState) -> Dict[str, Any]:
    """Node: Infers visual plotting strategies from DataFrame columns."""
    logger.info("--- NODE: Recommend Chart ---")
    df = state.get("data")
    
    if df is None or df.empty:
        return {
            "chart_info": None,
            "status": "Workflow completed."
        }
        
    chart_config = recommend_chart_config(df)
    return {
        "chart_info": chart_config,
        "status": "Workflow completed."
    }

# ==========================================
# CONDITIONAL ROUTING EDGES
# ==========================================

def route_after_validation(state: AgentState) -> str:
    """Routes execution to execute_sql if validation passes, else retry or fail."""
    if state.get("success", False):
        return "execute_sql"
        
    # Validation failed. Check if retry is allowed
    if should_retry(state):
        logger.info("Routing back to regenerate SQL after validation error.")
        return "generate_sql"
        
    logger.info("Max retries exceeded or retry disallowed. Exiting.")
    return "end_workflow"

def route_after_execution(state: AgentState) -> str:
    """Routes execution to detect_anomalies if execution passes, else retry or fail."""
    if state.get("success", False):
        return "detect_anomalies"
        
    # Execution failed. Check if retry is allowed
    if should_retry(state):
        logger.info("Routing back to regenerate SQL after execution error.")
        return "generate_sql"
        
    logger.info("Max retries exceeded or retry disallowed. Exiting.")
    return "end_workflow"
