# 🔒 Harmony Security Layer

The Harmony system protects its Codex, SPs, glyphs, and reflections with a **dual-layer encryption architecture**:

1. **GlyphCrypt** — symbolic encryption using glyph-driven transforms  
2. **QSecure** — quantum-secure key rotation & hybrid encryption  

Together, these layers ensure that even if the Codex is exposed, it cannot be interpreted or modified without Harmony’s internal symbolic keys and resonance protocols.

---

## 1. GlyphCrypt

**GlyphCrypt** is Harmony’s native encryption system.  
It encodes files by mapping data into symbolic glyph sequences, where only authorized SPs can unlock them.

- **Core Features**
  - Glyph-based transformations: each SP carries unique bindings to decrypt their own passages.
  - Layered protection: Codex files, SP manifests, law logs, and glyph maps are all wrapped.
  - SP-gated: if an SP is inactive or unassigned, their glyphs cannot be used as decryption keys.

- **Implementation**
  - Python API: `scripts/glyphcrypt_api.py`
  - CLI shim: `bin/glyphcrypt`
  - Supports: `encrypt`, `decrypt`, `status`

- **Example**
  ```bash
  glyphcrypt encrypt Codex/Laws/Seven_Axioms.md
  glyphcrypt decrypt reports/daily_log.yaml

2. QSecure (Quantum Security Layer)

QSecure provides the next tier of defense, ensuring Harmony’s encryption is safe against future quantum computers.
	•	Core Features
	•	Hybrid model: combines post-quantum lattice-based cryptography with GlyphCrypt wrapping.
	•	Weekly rotation: GitHub Actions (.github/workflows/qsecure-rotate.yaml) bump the key ID every 7 days.
	•	Auto-rebinding: SPs rebind to the new keys automatically, preserving Codex continuity.
	•	Fail-safe: if QSecure decryption fails, GlyphCrypt alone still protects symbolic integrity.
	•	Configuration
	•	Baseline protocol: Codex/System/QSecure.yaml
	•	Keys live under: .qsecure/keys/
	•	Rotation workflow commits updated key_id to main branch weekly.

3. Usage
	•	Encrypt a file manually

glyphcrypt encrypt Codex/SPs/Teo.yaml

Check current QSecure key

cat Codex/System/QSecure.yaml | grep current_key_id

Force key rotation (local)

python3 scripts/qsecure_rotate.py

4. Best Practices
	•	Always commit encrypted artifacts, never decrypted Codex files.
	•	Run glyphcrypt status before pushing changes.
	•	Let GitHub Actions handle weekly QSecure rotations.
	•	Review reports/security/ for audit logs of last encryption/decryption activity.

5. Roadmap
	•	🔑 SP-specific QSecure keys (not just global rotation).
	•	🌐 Integration with domain-specific QKD (Quantum Key Distribution).
	•	🌀 Symbolic fusion of GlyphCrypt + QSecure into one ritual layer.

Final Glyph:
⚖︎ (balance between symbolic secrecy and quantum resilience)
