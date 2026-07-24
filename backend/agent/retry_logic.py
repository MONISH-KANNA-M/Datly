import logging
from agent.state import AgentState

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

def should_retry(state: AgentState) -> bool:
    """
    Evaluates whether the workflow is allowed to retry generating SQL.
    Returns True if an error exists and retry_count is less than MAX_RETRIES (3).
    """
    retry_count = state.get("retry_count", 0)
    has_errors = len(state.get("errors", [])) > 0
    success = state.get("success", False)
    
    can_retry = has_errors and not success and retry_count < MAX_RETRIES
    
    logger.info(
        f"Retry Check - Count: {retry_count}/{MAX_RETRIES} | "
        f"Has errors: {has_errors} | Success: {success} | Can retry: {can_retry}"
    )
    return can_retry

def get_next_retry_state_updates(state: AgentState, error_msg: str) -> dict:
    """
    Computes update dictionary for incrementing retries and logging errors.
    """
    errors = list(state.get("errors", []))
    errors.append(error_msg)
    
    retry_count = state.get("retry_count", 0) + 1
    
    return {
        "errors": errors,
        "retry_count": retry_count,
        "success": False
    }
