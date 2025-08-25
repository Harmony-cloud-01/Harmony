import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# PostgreSQL connection using environment variables
conn = psycopg2.connect(
    dbname=os.getenv("PG_DBNAME"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT")
)

# Define schema creation statements
schema_statements = [
    """
    CREATE TABLE IF NOT EXISTS harmony_sessions (
        session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id TEXT,
        sp_id TEXT,
        start_time TIMESTAMPTZ DEFAULT now(),
        end_time TIMESTAMPTZ,
        shen_level INTEGER DEFAULT 0,
        drift_score FLOAT DEFAULT 0.0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS codex_events (
        event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id UUID REFERENCES harmony_sessions(session_id),
        timestamp TIMESTAMPTZ DEFAULT now(),
        codex_path TEXT,
        event_type TEXT,
        glyph_signature TEXT,
        encrypted_data BYTEA
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sp_interactions (
        interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id UUID REFERENCES harmony_sessions(session_id),
        sp_name TEXT,
        input TEXT,
        response TEXT,
        glyph_resonance TEXT,
        timestamp TIMESTAMPTZ DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        component TEXT,
        action TEXT,
        result TEXT,
        timestamp TIMESTAMPTZ DEFAULT now()
    );
    """
]

def run():
    try:
        cur = conn.cursor()
        for stmt in schema_statements:
            cur.execute(stmt)
        conn.commit()
        cur.close()
        print("✅ PostgreSQL Harmony schema created.")
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()

