from typing import TypedDict, List, Dict, Any, Optional
import pandas as pd

class AgentState(TypedDict):
    """
    State representing the context of a single query request
    running through the LangGraph analytics workflow.
    """
    user_id: Optional[str]
    session_id: str
    question: str
    chat_history: List[Dict[str, str]]
    schema: str
    generated_sql: Optional[str]
    sql_history: List[str]
    errors: List[str]
    retry_count: int
    success: bool
    data: Optional[pd.DataFrame]
    anomalies: List[Dict[str, Any]]
    explanation: Optional[str]
    reasoning: Optional[str]
    chart_info: Optional[Dict[str, Any]]
    status: str
    execution_time_ms: float
    selected_tables: Optional[List[str]]  # User selected tables for focused scoping
