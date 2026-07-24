import pytest
from tools.validator import validate_sql

def test_allowed_select_queries():
    # Basic SELECT
    is_valid, msg = validate_sql("SELECT * FROM customers")
    assert is_valid is True
    
    # Nested SELECT with alias
    is_valid, msg = validate_sql("SELECT name, (SELECT SUM(amount) FROM orders WHERE orders.customer_id = customers.id) FROM customers")
    assert is_valid is True
    
    # JOINs and grouping
    is_valid, msg = validate_sql("""
        SELECT c.name, SUM(o.amount) 
        FROM customers c 
        JOIN orders o ON c.id = o.customer_id 
        GROUP BY c.name
    """)
    assert is_valid is True

def test_allowed_cte_queries():
    # Common Table Expression
    is_valid, msg = validate_sql("""
        WITH monthly_sales AS (
            SELECT customer_id, SUM(amount) as total
            FROM orders
            GROUP BY customer_id
        )
        SELECT * FROM monthly_sales JOIN customers ON customers.id = monthly_sales.customer_id
    """)
    assert is_valid is True

def test_blocked_mutating_queries():
    # DROP
    is_valid, msg = validate_sql("DROP TABLE customers")
    assert is_valid is False
    assert "blocked" in msg.lower() or "banned" in msg.lower()
    
    # DELETE
    is_valid, msg = validate_sql("DELETE FROM orders WHERE id = 1")
    assert is_valid is False
    assert "blocked" in msg.lower() or "banned" in msg.lower()
    
    # INSERT
    is_valid, msg = validate_sql("INSERT INTO customers (name) VALUES ('Hacker')")
    assert is_valid is False
    
    # UPDATE
    is_valid, msg = validate_sql("UPDATE orders SET amount = 0.0 WHERE customer_id = 1")
    assert is_valid is False

def test_blocked_ddl_and_admin_commands():
    # ALTER
    is_valid, msg = validate_sql("ALTER TABLE customers ADD COLUMN hack TEXT")
    assert is_valid is False
    
    # PRAGMA modification
    is_valid, msg = validate_sql("PRAGMA foreign_keys = OFF")
    assert is_valid is False
    
    # ATTACH
    is_valid, msg = validate_sql("ATTACH DATABASE 'test.db' AS test")
    assert is_valid is False

def test_comment_bypass_attempts():
    # Injection hidden behind comment
    is_valid, msg = validate_sql("""
        SELECT * FROM orders; -- DROP TABLE customers;
    """)
    # Our validator strips comments and parses statements.
    # If the DROP is parsed as a second statement, it's evaluated.
    # If it is inside a comment, it's stripped.
    # Let's test standard comments are stripped:
    is_valid, msg = validate_sql("SELECT * FROM customers /* This is a comment */")
    assert is_valid is True
