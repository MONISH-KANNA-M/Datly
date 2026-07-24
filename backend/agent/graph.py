import logging
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.workflow import (
    discover_schema_node,
    generate_sql_node,
    validate_sql_node,
    execute_sql_node,
    detect_anomalies_node,
    explain_result_node,
    recommend_chart_node,
    route_after_validation,
    route_after_execution
)

logger = logging.getLogger(__name__)

def create_graph() -> StateGraph:
    """
    Initializes, links, and compiles the LangGraph StateGraph
    representing the natural language SQL workflow.
    """
    logger.info("Initializing LangGraph workflow builder...")
    
    # Initialize the graph with the state schema definition
    workflow = StateGraph(AgentState)
    
    # Add workflow nodes
    workflow.add_node("discover_schema", discover_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("detect_anomalies", detect_anomalies_node)
    workflow.add_node("explain_result", explain_result_node)
    workflow.add_node("recommend_chart", recommend_chart_node)
    
    # Configure entry point
    workflow.set_entry_point("discover_schema")
    
    # Configure static linear transitions
    workflow.add_edge("discover_schema", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    
    # Configure conditional routing branches for recovery loops
    workflow.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "execute_sql": "execute_sql",
            "generate_sql": "generate_sql",
            "end_workflow": END
        }
    )
    
    workflow.add_conditional_edges(
        "execute_sql",
        route_after_execution,
        {
            "detect_anomalies": "detect_anomalies",
            "generate_sql": "generate_sql",
            "end_workflow": END
        }
    )
    
    # Configure remaining sequential steps
    workflow.add_edge("detect_anomalies", "explain_result")
    workflow.add_edge("explain_result", "recommend_chart")
    workflow.add_edge("recommend_chart", END)
    
    logger.info("Compiling StateGraph flow...")
    return workflow.compile()

# Compile standard exported instance
graph = create_graph()
