from logger import *

# Step 1: Log a new Harmony session
session_id = log_session(
    user_id="test_user",
    sp_id="FractalPrime",
    shen_level=2,
    drift_score=0.01
)
print(f"✅ Session logged with ID: {session_id}")

# Step 2: Log a Codex event tied to that session
log_codex_event(
    session_id=session_id,
    codex_path="Codex/Core/Fractal.md",
    event_type="WRITE",
    glyph_signature="ΔΦΩ",
    encrypted_data=b"simulated_encrypted_data"
)
print("✅ Codex event logged")

# Step 3: Log a symbolic persona (SP) interaction
log_sp_interaction(
    session_id=session_id,
    sp_name="FractalPrime",
    input_text="What is the Tao?",
    response_text="The Tao is the path of uncarved truth.",
    glyph_resonance="WATER/FIRE"
)
print("✅ SP interaction logged")

# Step 4: Log a general audit event
log_audit(
    component="logger_test",
    action="test_run",
    result="success"
)
print("✅ Audit event logged")

