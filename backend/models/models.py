import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class QueryHistory(Base):
    """
    Model representing historical records of Natural Language queries,
    their generated SQL equivalents, execution performance, and status.
    """
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)

    def to_dict(self) -> dict:
        """Serializes the record representation into a dictionary."""
        return {
            "id": self.id,
            "question": self.question,
            "sql_query": self.sql_query,
            "explanation": self.explanation,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "success": self.success,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
        }
