import os
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import urllib.parse as urlparse
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

DEFAULT_PG_URL = "postgresql://postgres:postgres@localhost:5432/analytics_gpt"
FALLBACK_SQLITE_URL = "sqlite:///database/fallback_user_data.db"

def create_db_if_not_exists(db_url: str):
    """
    Connects to the default 'postgres' database and creates the target database
    if it does not already exist.
    """
    if not db_url.startswith("postgresql"):
        return
    try:
        result = urlparse.urlparse(db_url)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port or 5432
        
        # Connect to default database 'postgres' to run CREATE DATABASE
        con = psycopg2.connect(
            dbname='postgres',
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (database,))
        exists = cur.fetchone()
        if not exists:
            logger.info(f"Database '{database}' does not exist. Creating database...")
            # SQL identifiers like database name cannot be parameterized, but we get it from env.
            # We sanitize by making sure it matches standard alphanumeric/underscore DB name format.
            safe_db_name = "".join(c for c in database if c.isalnum() or c == "_")
            cur.execute(f"CREATE DATABASE {safe_db_name}")
            logger.info(f"Database '{database}' created successfully.")
        cur.close()
        con.close()
    except Exception as e:
        logger.warning(f"Could not auto-create database via PostgreSQL default connector: {str(e)}")

def get_db_url() -> str:
    """Retrieves the database connection URL from environment variables, fallback to SQLite if needed."""
    url = os.getenv("DATABASE_URL")
    if not url:
        logger.warning("DATABASE_URL not found in environment variables. Falling back to local SQLite database.")
        os.makedirs("database", exist_ok=True)
        return FALLBACK_SQLITE_URL
    return url.strip()

def get_engine():
    """Initializes and returns the SQLAlchemy database engine."""
    db_url = get_db_url()
    
    # Try to auto-create the PostgreSQL database if it doesn't exist
    if db_url.startswith("postgresql"):
        create_db_if_not_exists(db_url)
        
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        
    try:
        engine = create_engine(db_url, connect_args=connect_args)
        # Test connection to ensure PostgreSQL works (if configured)
        if not db_url.startswith("sqlite"):
            with engine.connect() as conn:
                pass
        return engine
    except Exception as e:
        logger.error(f"Failed to connect to the configured database ({db_url}): {str(e)}")
        if db_url != FALLBACK_SQLITE_URL:
            logger.warning("Falling back to local SQLite database due to connection failure.")
            os.makedirs("database", exist_ok=True)
            return create_engine(FALLBACK_SQLITE_URL, connect_args={"check_same_thread": False})
        raise e

# Create SessionLocal bound to the engine
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session() -> Generator[Session, None, None]:
    """
    Context generator for DB sessions.
    Ensures sessions are closed properly after execution.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction error: {str(e)}")
        raise e
    finally:
        session.close()

def init_pg_db() -> None:
    """Initializes the database by creating all standard tables."""
    from models.pg_models import Base
    try:
        Base.metadata.create_all(bind=get_engine())
        logger.info("PostgreSQL/Fallback Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL/Fallback Database: {str(e)}")
        raise e
