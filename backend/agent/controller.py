import logging
import time
import pandas as pd
from typing import Dict, Any, List
from agent.graph import graph
from agent.state import AgentState
from database.pg_db import get_session
from models.pg_models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

def get_history_for_session(session_id: str) -> List[Dict[str, str]]:
    """Loads past chat history for the given session to feed to the LLM prompt."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        messages = db.query(ChatMessage).filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
        return [{"role": msg.role, "text": msg.text} for msg in messages]
    except Exception as e:
        logger.error(f"Failed to fetch history for session {session_id}: {str(e)}")
        return []
    finally:
        db.close()

def save_chat_turn(session_id: str, question: str, response_state: Dict[str, Any]) -> None:
    """Saves both the user question and the assistant response (with analytics meta) into PostgreSQL."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        # 1. Save User message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            text=question
        )
        db.add(user_msg)
        
        # Determine assistant text response
        assistant_text = response_state.get("explanation")
        if not assistant_text and response_state.get("errors"):
            assistant_text = f"An error occurred: {response_state['errors'][-1]}"
        elif not assistant_text:
            assistant_text = "I couldn't generate an answer for this question."

        # Convert DataFrame to serializable structure if exists
        df = response_state.get("data")
        raw_data = None
        if isinstance(df, pd.DataFrame):
            raw_data = df.to_dict(orient="records")

        # 2. Save Assistant message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            text=assistant_text,
            sql_query=response_state.get("generated_sql"),
            reasoning=response_state.get("reasoning"),
            anomalies=response_state.get("anomalies", []),
            chart_info=response_state.get("chart_info"),
            data=raw_data,
            execution_time_ms=response_state.get("execution_time_ms", 0.0)
        )
        db.add(assistant_msg)
        db.commit()
        logger.info(f"Saved chat messages for session {session_id} to PostgreSQL.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save chat turn in PostgreSQL: {str(e)}")
    finally:
        db.close()

def run_analytics_agent(user_id: str, session_id: str, question: str, selected_tables: List[str] = None) -> Dict[str, Any]:
    """
    Invokes the compiled LangGraph workflow to answer a question under user scoping.
    Loads previous session context, executes the agent steps, and persists messages.
    """
    logger.info(f"Controller invoking agent for user: {user_id}, session: {session_id}, query: '{question}', selected_tables: {selected_tables}")
    start_time = time.perf_counter()
    
    # 1. Fetch chat history context
    chat_history = get_history_for_session(session_id)
    
    # 2. Setup initial graph state with user isolation context
    initial_state: AgentState = {
        "user_id": user_id,
        "session_id": session_id,
        "question": question,
        "chat_history": chat_history,
        "schema": "",
        "generated_sql": None,
        "sql_history": [],
        "errors": [],
        "retry_count": 0,
        "success": False,
        "data": None,
        "anomalies": [],
        "explanation": None,
        "reasoning": None,
        "chart_info": None,
        "status": "Initializing workflow...",
        "execution_time_ms": 0.0,
        "selected_tables": selected_tables
    }
    
    try:
        # Run graph
        final_state = graph.invoke(initial_state)
        
        elapsed_time = (time.perf_counter() - start_time) * 1000.0
        final_state["execution_time_ms"] = elapsed_time
        logger.info(f"LangGraph execution completed in {elapsed_time:.2f}ms.")
        
        # Save turns
        save_chat_turn(session_id, question, final_state)
        
        # Convert DataFrame to serializable list of dicts
        df = final_state.get("data")
        serializable_data = None
        if isinstance(df, pd.DataFrame):
            serializable_data = df.to_dict(orient="records")
            
        return {
            "success": final_state.get("success", False),
            "generated_sql": final_state.get("generated_sql"),
            "sql_history": final_state.get("sql_history", []),
            "errors": final_state.get("errors", []),
            "retry_count": final_state.get("retry_count", 0),
            "data": serializable_data,
            "anomalies": final_state.get("anomalies", []),
            "explanation": final_state.get("explanation"),
            "reasoning": final_state.get("reasoning"),
            "chart_info": final_state.get("chart_info"),
            "schema": final_state.get("schema"),
            "execution_time_ms": elapsed_time
        }
        
    except Exception as e:
        elapsed_time = (time.perf_counter() - start_time) * 1000.0
        logger.error(f"Workflow execution failed: {str(e)}")
        error_state = {
            "success": False,
            "generated_sql": None,
            "sql_history": [],
            "errors": [f"Critical workflow failure: {str(e)}"],
            "retry_count": 0,
            "data": None,
            "anomalies": [],
            "explanation": "Could not complete analysis due to an internal system error.",
            "reasoning": "A system crash occurred before logic execution.",
            "chart_info": None,
            "schema": "",
            "execution_time_ms": elapsed_time
        }
        
        save_chat_turn(session_id, question, error_state)
        return error_state
