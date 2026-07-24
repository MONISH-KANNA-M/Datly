import datetime
import json
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    """
    Model representing an Application User synced from Clerk.
    ID is a String containing Clerk's user ID (e.g., 'user_2xyz').
    """
    __tablename__ = "users"

    id = Column(String(100), primary_key=True)  # Clerk User ID
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    files = relationship("UploadedFile", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ChatSession(Base):
    """
    Model representing a Chat Session/Thread belonging to a Clerk User.
    """
    __tablename__ = "chat_sessions"

    id = Column(String(50), primary_key=True)  # UUID or random string
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False, default="New Chat")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ChatMessage(Base):
    """
    Model representing individual messages within a chat session.
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    text = Column(Text, nullable=False)
    
    # AI metadata fields (nullable for user messages)
    sql_query = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    anomalies_json = Column(Text, nullable=True)  # Serialized JSON list
    chart_info_json = Column(Text, nullable=True) # Serialized JSON dict
    data_json = Column(Text, nullable=True)       # Serialized JSON list of records (results)
    execution_time_ms = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")

    @property
    def anomalies(self):
        if self.anomalies_json:
            try:
                return json.loads(self.anomalies_json)
            except Exception:
                return []
        return []

    @anomalies.setter
    def anomalies(self, value):
        if value is not None:
            self.anomalies_json = json.dumps(value)
        else:
            self.anomalies_json = None

    @property
    def chart_info(self):
        if self.chart_info_json:
            try:
                return json.loads(self.chart_info_json)
            except Exception:
                return None
        return None

    @chart_info.setter
    def chart_info(self, value):
        if value is not None:
            self.chart_info_json = json.dumps(value)
        else:
            self.chart_info_json = None

    @property
    def data(self):
        if self.data_json:
            try:
                return json.loads(self.data_json)
            except Exception:
                return []
        return []

    @data.setter
    def data(self, value):
        if value is not None:
            self.data_json = json.dumps(value)
        else:
            self.data_json = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "text": self.text,
            "sql_query": self.sql_query,
            "reasoning": self.reasoning,
            "anomalies": self.anomalies,
            "chart_info": self.chart_info,
            "data": self.data,  # Include serialized query results
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class UploadedFile(Base):
    """
    Model representing metadata for uploaded files loaded into DuckDB, scoped to a Clerk User.
    """
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    filename = Column(String(255), nullable=False)
    table_name = Column(String(100), nullable=False, unique=True)
    file_path = Column(String(512), nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    columns_json = Column(Text, nullable=True)  # Serialized JSON list
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="files")

    @property
    def columns(self):
        if self.columns_json:
            try:
                return json.loads(self.columns_json)
            except Exception:
                return []
        return []

    @columns.setter
    def columns(self, value):
        if value is not None:
            self.columns_json = json.dumps(value)
        else:
            self.columns_json = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "table_name": self.table_name,
            "file_path": self.file_path,
            "row_count": self.row_count,
            "columns": self.columns,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class DashboardWidget(Base):
    """
    Model representing user-saved dashboard widgets (metrics or charts).
    """
    __tablename__ = "dashboard_widgets"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    widget_type = Column(String(50), nullable=False)  # 'metric' or 'chart'
    config_json = Column(Text, nullable=True)         # Chart config (x_axis, y_axis, type)
    data_json = Column(Text, nullable=True)           # Serialized metric/chart dataset
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User")

    @property
    def config(self):
        if self.config_json:
            try:
                return json.loads(self.config_json)
            except Exception:
                return {}
        return {}

    @config.setter
    def config(self, value):
        self.config_json = json.dumps(value) if value is not None else None

    @property
    def data(self):
        if self.data_json:
            try:
                return json.loads(self.data_json)
            except Exception:
                return []
        return []

    @data.setter
    def data(self, value):
        self.data_json = json.dumps(value) if value is not None else None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "widget_type": self.widget_type,
            "config": self.config,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class QueryResultCache(Base):
    """
    Model representing query cache entries scoped to a user to prevent redundant LLM runs.
    """
    __tablename__ = "query_result_caches"

    query_hash = Column(String(64), primary_key=True)  # SHA256 hash of (question + selected_tables)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sql_query = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    anomalies_json = Column(Text, nullable=True)
    chart_info_json = Column(Text, nullable=True)
    result_data_json = Column(Text, nullable=True)     # Serialized query result records
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User")

    @property
    def anomalies(self):
        if self.anomalies_json:
            try:
                return json.loads(self.anomalies_json)
            except Exception:
                return []
        return []

    @anomalies.setter
    def anomalies(self, value):
        self.anomalies_json = json.dumps(value) if value is not None else None

    @property
    def chart_info(self):
        if self.chart_info_json:
            try:
                return json.loads(self.chart_info_json)
            except Exception:
                return {}
        return {}

    @chart_info.setter
    def chart_info(self, value):
        self.chart_info_json = json.dumps(value) if value is not None else None

    @property
    def result_data(self):
        if self.result_data_json:
            try:
                return json.loads(self.result_data_json)
            except Exception:
                return []
        return []

    @result_data.setter
    def result_data(self, value):
        self.result_data_json = json.dumps(value) if value is not None else None

    def to_dict(self) -> dict:
        return {
            "query_hash": self.query_hash,
            "user_id": self.user_id,
            "sql_query": self.sql_query,
            "explanation": self.explanation,
            "reasoning": self.reasoning,
            "anomalies": self.anomalies,
            "chart_info": self.chart_info,
            "data": self.result_data,
            "cached": True,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
