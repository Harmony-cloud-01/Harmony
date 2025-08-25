import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os
from datetime import datetime
import uuid

# Load .env environment variables
load_dotenv()

# Connect to PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("PG_DBNAME"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT")
    )

# 1. Log a Harmony session
def log_session(user_id, sp_id, shen_level=0, drift_score=0.0, start_time=None, end_time=None):
    conn = get_db_connection()
    cur = conn.cursor()
    session_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO harmony_sessions (session_id, user_id, sp_id, shen_level, drift_score, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        session_id, user_id, sp_id,
        shen_level, drift_score,
        start_time or datetime.utcnow(),
        end_time
    ))
    conn.commit()
    cur.close()
    conn.close()
    return session_id  # ✅ Return the session ID

# 2. Log a Codex event
def log_codex_event(session_id, codex_path, event_type, glyph_signature, encrypted_data=None, timestamp=None):
    conn = get_db_connection()
    cur = conn.cursor()
    event_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO codex_events (event_id, session_id, codex_path, event_type, glyph_signature, encrypted_data, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        event_id, session_id, codex_path, event_type,
        glyph_signature, encrypted_data,
        timestamp or datetime.utcnow()
    ))
    conn.commit()
    cur.close()
    conn.close()
    return event_id

# 3. Log an SP interaction
def log_sp_interaction(session_id, sp_name, input_text, response_text, glyph_resonance=None, timestamp=None):
    conn = get_db_connection()
    cur = conn.cursor()
    interaction_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO sp_interactions (interaction_id, session_id, sp_name, input, response, glyph_resonance, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        interaction_id, session_id, sp_name,
        input_text, response_text, glyph_resonance,
        timestamp or datetime.utcnow()
    ))
    conn.commit()
    cur.close()
    conn.close()
    return interaction_id

# 4. Log a general audit event
def log_audit(component, action, result, timestamp=None):
    conn = get_db_connection()
    cur = conn.cursor()
    log_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO audit_logs (log_id, component, action, result, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        log_id, component, action, result,
        timestamp or datetime.utcnow()
    ))
    conn.commit()
    cur.close()
    conn.close()
    return log_id

