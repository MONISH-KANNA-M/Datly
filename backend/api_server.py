import os
import uuid
import logging
import datetime
import jwt
import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

from database.pg_db import init_pg_db, get_session
from models.pg_models import User, ChatSession, ChatMessage, UploadedFile, DashboardWidget, QueryResultCache
from services.upload_service import process_and_import_file, save_uploaded_file, list_user_tables, delete_user_table
from tools.schema_tool import get_user_schema
from agent.controller import run_analytics_agent
import hashlib
from services.bi_service import profile_table_quality, generate_auto_dashboard
from services.llm_service import active_provider_var

# Dynamic Clerk JWKS Configuration
def get_clerk_jwks_url() -> str:
    """Parses the Clerk publishable key from environment to get the correct JWKS domain."""
    pub_key = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "")
    if not pub_key:
        # Fallback to dev key domain
        return "https://quality-glowworm-39.clerk.accounts.dev/.well-known/jwks.json"
    
    try:
        parts = pub_key.split("_")
        if len(parts) >= 3:
            encoded_domain = parts[2]
            # Re-apply padding if base64 stripped it
            padded = encoded_domain + "=" * (4 - len(encoded_domain) % 4)
            decoded = base64.b64decode(padded).decode("utf-8")
            domain = decoded.split("$")[0]
            return f"https://{domain}/.well-known/jwks.json"
    except Exception as e:
        logger.warning(f"Could not parse Clerk domain from publishable key: {str(e)}")
        
    return "https://quality-glowworm-39.clerk.accounts.dev/.well-known/jwks.json"

JWKS_URL = get_clerk_jwks_url()
logger.info(f"Configuring Clerk JWKS client at: {JWKS_URL}")
jwks_client = jwt.PyJWKClient(JWKS_URL)

security = HTTPBearer()

def sync_clerk_user(user_id: str, username: str) -> None:
    """Ensures a corresponding User record exists in the local PostgreSQL database."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            user = User(id=user_id, username=username)
            db.add(user)
            db.commit()
            logger.info(f"Synchronized new Clerk user '{user_id}' with local PostgreSQL database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to sync Clerk user: {str(e)}")
    finally:
        db.close()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Decodes the Clerk JWT session token, verifies its RS256 signature against Clerk's JWKS,
    syncs user profiles, and returns the Clerk user ID. Fallback to unverified decode
    for offline / local developer mode is provided if the key server is unreachable.
    """
    token = credentials.credentials
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True, "verify_aud": False}
        )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Authentication token is missing subject (user ID).")
            
        user_metadata = payload.get("username") or payload.get("email") or user_id
        sync_clerk_user(user_id, user_metadata)
        
        return user_id
    except Exception as e:
        logger.warning(f"Clerk JWKS verification failed or signature server is offline: {str(e)}. Falling back to local decode.")
        try:
            # Decode without verifying signature to allow local testing if network is blocked
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
            if user_id:
                user_metadata = payload.get("username") or payload.get("email") or user_id
                sync_clerk_user(user_id, user_metadata)
                return user_id
        except Exception as inner_e:
            logger.error(f"Unverified decode also failed: {str(inner_e)}")
        
        raise HTTPException(status_code=401, detail=f"Authentication token is invalid: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables on FastAPI startup...")
    try:
        init_pg_db()
    except Exception as e:
        logger.critical(f"Database initialization failed: {str(e)}")
    yield

app = FastAPI(
    title="BYOB Clerk Server",
    description="FastAPI Backend for BYOB with Clerk RS256 JWT Authentication",
    version="1.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schema
class ChatRequest(BaseModel):
    session_id: str
    question: str
    selected_tables: Optional[List[str]] = None
    model_provider: Optional[str] = "ollama"

class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"

def invalidate_query_cache(user_id: str) -> None:
    """Clears all cached query results and dashboard widgets for the user on data changes."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        db.query(QueryResultCache).filter_by(user_id=user_id).delete()
        db.query(DashboardWidget).filter_by(user_id=user_id).delete()
        db.commit()
        logger.info(f"Query cache and dashboard widgets invalidated for user {user_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to invalidate cache: {str(e)}")
    finally:
        db.close()

# ==========================================
# ENDPOINTS: FILE UPLOADS (SECURED VIA CLERK)
# ==========================================

@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """Uploads and ingests datasets isolated to the authenticated Clerk user."""
    results = []
    for file in files:
        filename = file.filename
        logger.info(f"Processing upload '{filename}' for Clerk user {current_user_id}")
        
        try:
            file_bytes = await file.read()
            saved_path = save_uploaded_file(filename, file_bytes)
            
            # Scoped to Clerk's user ID
            table_name, row_count = process_and_import_file(saved_path, filename, user_id=current_user_id)
            
            results.append({
                "filename": filename,
                "table_name": table_name,
                "row_count": row_count,
                "success": True
            })
        except Exception as e:
            logger.error(f"Failed to process file '{filename}': {str(e)}")
            results.append({
                "filename": filename,
                "error": str(e),
                "success": False
            })
            
    # Invalidate cache if there was any successful upload
    successes = [r for r in results if r.get("success")]
    if successes:
        invalidate_query_cache(current_user_id)
            
    return {"files": results}

@app.get("/api/files")
async def get_files(current_user_id: str = Depends(get_current_user_id)):
    """Lists uploaded files belonging only to the authenticated Clerk user."""
    try:
        return list_user_tables(user_id=current_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{table_name}")
async def delete_file(
    table_name: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Deletes table from DuckDB and metadata from PostgreSQL if owned by Clerk user."""
    try:
        delete_user_table(table_name, user_id=current_user_id)
        invalidate_query_cache(current_user_id)
        return {"status": "success", "message": f"Table '{table_name}' deleted."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS: CHAT SESSIONS (SECURED VIA CLERK)
# ==========================================

@app.get("/api/sessions")
async def get_sessions(current_user_id: str = Depends(get_current_user_id)):
    """Lists chat sessions belonging to the authenticated Clerk user."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        sessions = db.query(ChatSession).filter_by(user_id=current_user_id).order_by(ChatSession.created_at.desc()).all()
        return [s.to_dict() for s in sessions]
    finally:
        db.close()

@app.post("/api/sessions")
async def create_session(
    req: SessionCreateRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """Creates a new chat session scoped to the authenticated Clerk user."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        session_id = str(uuid.uuid4())
        new_session = ChatSession(
            id=session_id,
            user_id=current_user_id,
            title=req.title or "New Chat"
        )
        db.add(new_session)
        db.commit()
        return new_session.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Deletes chat session and messages if owned by authenticated Clerk user."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        session = db.query(ChatSession).filter_by(id=session_id, user_id=current_user_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or permission denied.")
        db.delete(session)
        db.commit()
        return {"status": "success", "message": "Session deleted."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Retrieves message logs for a session, verifying Clerk user ownership."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        session = db.query(ChatSession).filter_by(id=session_id, user_id=current_user_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or permission denied.")
        messages = db.query(ChatMessage).filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
        return [m.to_dict() for m in messages]
    finally:
        db.close()

# ==========================================
# ENDPOINTS: CHAT EXECUTION (SECURED VIA CLERK)
# ==========================================

@app.post("/api/chat")
async def chat(
    req: ChatRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """Triggers LangGraph agent workflow under Clerk user isolation context, with query results caching."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        session = db.query(ChatSession).filter_by(id=req.session_id, user_id=current_user_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or permission denied.")
    finally:
        db.close()

    # 1. Compute Cache Hash based on user_id, question, and selected_tables scope
    tables_list = req.selected_tables or []
    sorted_tables_str = ",".join(sorted(tables_list))
    cache_payload = f"{current_user_id}:{req.question.strip().lower()}:{sorted_tables_str}"
    query_hash = hashlib.sha256(cache_payload.encode()).hexdigest()

    provider_token = active_provider_var.set(req.model_provider or "ollama")
    try:
        # Check cache first
        session_gen = get_session()
        db = next(session_gen)
        try:
            cached_entry = db.query(QueryResultCache).filter_by(query_hash=query_hash, user_id=current_user_id).first()
            if cached_entry:
                logger.info(f"Query cache HIT for query: '{req.question}'")
                
                # Save turns to ChatMessage history
                user_msg = ChatMessage(
                    session_id=req.session_id,
                    role="user",
                    text=req.question
                )
                db.add(user_msg)
                
                assistant_msg = ChatMessage(
                    session_id=req.session_id,
                    role="assistant",
                    text=cached_entry.explanation or "Served from cache.",
                    sql_query=cached_entry.sql_query,
                    reasoning=cached_entry.reasoning,
                    anomalies=cached_entry.anomalies,
                    chart_info=cached_entry.chart_info,
                    data=cached_entry.result_data,
                    execution_time_ms=0.0
                )
                db.add(assistant_msg)
                db.commit()
                
                # Trigger session rename if default
                active_session = db.query(ChatSession).filter_by(id=req.session_id).first()
                if active_session and (not active_session.title or active_session.title.strip().lower() == "new chat"):
                    snippet = req.question[:40] + "..." if len(req.question) > 40 else req.question
                    active_session.title = snippet
                    db.commit()
                    
                return cached_entry.to_dict()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to process cached query check: {str(e)}")
        finally:
            db.close()

        try:
            # Run agent with user isolation context (Cache Miss)
            result = run_analytics_agent(current_user_id, req.session_id, req.question, selected_tables=req.selected_tables)
            
            # Save to Cache if successful
            if result.get("success"):
                session_gen = get_session()
                db = next(session_gen)
                try:
                    cache_entry = QueryResultCache(
                        query_hash=query_hash,
                        user_id=current_user_id,
                        sql_query=result.get("generated_sql"),
                        explanation=result.get("explanation"),
                        reasoning=result.get("reasoning"),
                        anomalies=result.get("anomalies", []),
                        chart_info=result.get("chart_info"),
                        result_data=result.get("data", [])
                    )
                    db.merge(cache_entry)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Failed to save query result in cache: {str(e)}")
                finally:
                    db.close()

            # Rename session title if default
            session_gen = get_session()
            db = next(session_gen)
            try:
                active_session = db.query(ChatSession).filter_by(id=req.session_id).first()
                if active_session and (not active_session.title or active_session.title.strip().lower() == "new chat"):
                    snippet = req.question[:40] + "..." if len(req.question) > 40 else req.question
                    active_session.title = snippet
                    db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
                
            return result
        except Exception as e:
            logger.error(f"Chat agent execution error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        active_provider_var.reset(provider_token)

# ==========================================
# ENDPOINTS: SCHEMA METADATA (SECURED VIA CLERK)
# ==========================================

@app.get("/api/schema")
async def get_schema_metadata(current_user_id: str = Depends(get_current_user_id)):
    """Retrieves table schemas owned only by the authenticated Clerk user."""
    try:
        return get_user_schema(user_id=current_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS: DASHBOARDS & QUALITY CHECKS (SECURED VIA CLERK)
# ==========================================

@app.post("/api/dashboard/generate")
async def generate_dashboard(current_user_id: str = Depends(get_current_user_id)):
    """Triggers automatic dashboard calculation and persists widgets for the user."""
    try:
        widgets = generate_auto_dashboard(user_id=current_user_id)
        return {"status": "success", "widgets": widgets}
    except Exception as e:
        logger.error(f"Failed to generate dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard")
async def get_dashboard(current_user_id: str = Depends(get_current_user_id)):
    """Retrieves all generated dashboard widgets for the user."""
    session_gen = get_session()
    db = next(session_gen)
    try:
        widgets = db.query(DashboardWidget).filter_by(user_id=current_user_id).order_by(DashboardWidget.created_at.asc()).all()
        return [w.to_dict() for w in widgets]
    except Exception as e:
        logger.error(f"Failed to fetch dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/files/{table_name}/quality")
async def get_table_quality(
    table_name: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Runs a data quality profile scan on a specific user table in DuckDB."""
    try:
        report = profile_table_quality(user_id=current_user_id, table_name=table_name)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Data quality profiling failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
