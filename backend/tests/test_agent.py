import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from agent.controller import run_analytics_agent
from database.pg_db import init_pg_db
from models.pg_models import User, ChatSession

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Setup a sample test database for agent execution."""
    init_pg_db()
    
    # Ingest a mock table: customers
    df = pd.DataFrame({
        "id": [1, 2],
        "name": ["Alice", "Bob"],
        "city": ["New York", "Chicago"]
    })
    
    from database.duckdb_manager import import_df_to_duckdb
    import_df_to_duckdb(df, "u_test_user_id_1_customers") # user string prefix
    
    # Setup mock user and session in PostgreSQL
    from database.pg_db import get_session
    session_gen = get_session()
    db = next(session_gen)
    try:
        # Check if user with string id already exists
        user = db.query(User).filter_by(id="test_user_id_1").first()
        if not user:
            user = User(id="test_user_id_1", username="test_user")
            db.add(user)
            db.flush()
        
        # Check if session already exists
        session = db.query(ChatSession).filter_by(id="test_session_id").first()
        if not session:
            session = ChatSession(id="test_session_id", user_id="test_user_id_1", title="Test Session")
            db.add(session)
            db.commit()
        else:
            session.user_id = "test_user_id_1"
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
        
    yield

@patch("agent.workflow.generate_completion")
@patch("tools.explanation_tool.generate_completion")
def test_successful_agent_flow(mock_explain, mock_gen):
    """Tests that the agent discovers schema, generates correct SQL, and explains it."""
    # Mock SQL generation response (with thoughts and SQL)
    mock_gen.return_value = "<thoughts>\nLooking for customers in New York.\n</thoughts>\n```sql\nSELECT * FROM u_test_user_id_1_customers WHERE city = 'New York';\n```"
    # Mock explanation response
    mock_explain.return_value = "This query retrieves all customers located in New York. The results show Alice."

    result = run_analytics_agent("test_user_id_1", "test_session_id", "Show customers in New York")
    
    assert result["success"] is True
    assert result["generated_sql"] == "SELECT * FROM u_test_user_id_1_customers WHERE city = 'New York';"
    assert result["retry_count"] == 0
    assert result["data"] is not None
    assert len(result["data"]) == 1
    assert result["explanation"] == "This query retrieves all customers located in New York. The results show Alice."

@patch("agent.workflow.generate_completion")
@patch("tools.explanation_tool.generate_completion")
def test_agent_self_correction_loop(mock_explain, mock_gen):
    """
    Tests the self-correction loop where LLM generates bad SQL first,
    re-tries based on execution error, and succeeds on the second attempt.
    """
    # First call returns bad SQL (syntax error: double WHERE)
    # Second call returns corrected SQL
    mock_gen.side_effect = [
        "<thoughts>Thoughts</thoughts>\n```sql\nSELECT * FROM u_test_user_id_1_customers WHERE WHERE name = 'Alice';\n```",
        "<thoughts>Thoughts</thoughts>\n```sql\nSELECT * FROM u_test_user_id_1_customers WHERE name = 'Alice';\n```"
      ]
    mock_explain.return_value = "This explains the customer record for Alice."
    
    result = run_analytics_agent("test_user_id_1", "test_session_id", "Find customer named Alice")
    
    # Assert it retried and succeeded on 2nd attempt (retry_count = 1)
    assert result["success"] is True
    assert result["generated_sql"] == "SELECT * FROM u_test_user_id_1_customers WHERE name = 'Alice';"
    assert result["retry_count"] == 1
    assert len(result["errors"]) == 1
    assert result["data"] is not None
    assert len(result["data"]) == 1
