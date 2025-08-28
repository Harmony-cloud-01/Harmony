Quick wiring + usage
	1.	Add dependency
Append to requirements.txt:
cryptography>=42.0.0

	2.	Make executable

 chmod +x scripts/glyphcrypt.py

 	3.	Encrypt a file

  ./scripts/glyphcrypt.py encrypt Codex/Core/Definitions.yaml \
  --sp SP-ethos --shen 3 \
  --gate SP-ethos --gate SP-fractal-prime \
  --min-shen 2
# Produces Codex/Core/Definitions.yaml.gcrypt (and removes plaintext by default)

	4.	Inspect header

 ./scripts/glyphcrypt.py inspect Codex/Core/Definitions.yaml.gcrypt

 	5.	Decrypt

  ./scripts/glyphcrypt.py decrypt Codex/Core/Definitions.yaml.gcrypt \
  --sp SP-ethos --shen 3

  Optional integration hooks
	•	Add a pre-commit style helper (pseudo):

 # scripts/hook_encrypt_codex.sh
find Codex -type f \( -name "*.md" -o -name "*.yaml" \) \
  -not -name "*.gcrypt" -print0 | while IFS= read -r -d '' f; do
  ./scripts/glyphcrypt.py encrypt "$f" --sp SP-webmaster --shen 2 --gate SP-webmaster --min-shen 2
done

	•	Wire into your weekly tasks once you’re ready (after confirming workflows).

tiny, importable GlyphCrypt helper you can drop into the repo. It gives you a clean Python API for in-process use (merge scripts, audits, etc.) and uses openssl under the hood via subprocess (no extra deps). It also supports your ASCII armor header so the files stay human-legible.

File: SDK/glyphcrypt/api.py

# SDK/glyphcrypt/api.py
# Tiny helper for in-process use of GlyphCrypt:
# - HKDF-SHA256 key derivation from (passphrase, glyph_salt)
# - AES-256-GCM via openssl (stdin/stdout) to avoid third-party deps
# - ASCII armor header with metadata for safe storage/versioning

from __future__ import annotations
import base64
import hashlib
import hmac
import io
import json
import os
import re
import shutil
import subprocess
import textwrap
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

__all__ = [
    "GlyphCryptError",
    "GlyphCryptMeta",
    "derive_key_material",
    "is_armored",
    "parse_armor",
    "armor_pack",
    "armor_unpack",
    "seal_bytes",
    "open_bytes",
    "seal_file",
    "open_file",
]

HEADER_MARK = "### GlyphCrypt v1"
META_PREFIX = "## "
ARMOR_BEGIN = "-----BEGIN GLYPHCRYPT-----"
ARMOR_END = "------END GLYPHCRYPT------"

class GlyphCryptError(RuntimeError):
    pass

@dataclass
class GlyphCryptMeta:
    glyph_id: str                # e.g., "G-Ω-17"
    law_context: str             # e.g., "Harmonic Coherence"
    variant: str = "aes-256-gcm" # algorithm tag
    iter: int = 250_000          # PBKDF2/HKDF cost hint for header
    kdf: str = "hkdf-sha256"     # derivation label
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        d = {
            "glyph_id": self.glyph_id,
            "law": self.law_context,
            "variant": self.variant,
            "kdf": self.kdf,
            "iter": str(self.iter),
        }
        if self.comment:
            d["comment"] = self.comment
        return d

# ---------- HKDF (SHA-256) ----------

def _hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    return hmac.new(salt, ikm, hashlib.sha256).digest()

def _hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    # RFC 5869 HKDF-Expand
    out = b""
    t = b""
    counter = 1
    while len(out) < length:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
        out += t
        counter += 1
    return out[:length]

def derive_key_material(passphrase: str, glyph_salt: str, out_len: int = 48) -> bytes:
    """
    HKDF-SHA256(passphrase, salt=glyph_salt) → out_len bytes (32 key + 16 iv by default).
    """
    if not passphrase or not glyph_salt:
        raise GlyphCryptError("derive_key_material: passphrase and glyph_salt required")
    ikm = passphrase.encode("utf-8")
    salt = glyph_salt.encode("utf-8")
    prk = _hkdf_extract(salt, ikm)
    info = b"GlyphCrypt/v1"
    return _hkdf_expand(prk, info, out_len)

# ---------- ASCII Armor ----------

def armor_pack(meta: GlyphCryptMeta, ciphertext: bytes) -> bytes:
    meta_line = META_PREFIX + json.dumps(meta.to_dict(), ensure_ascii=False)
    b64 = base64.b64encode(ciphertext).decode("ascii")
    wrapped = textwrap.fill(b64, width=64)
    content = "\n".join([
        HEADER_MARK,
        meta_line,
        ARMOR_BEGIN,
        wrapped,
        ARMOR_END,
        "",  # newline at end
    ])
    return content.encode("utf-8")

_ARMOR_RE = re.compile(
    r"^### GlyphCrypt v1\s+## (.+?)\s+-----BEGIN GLYPHCRYPT-----\s+([A-Za-z0-9+/=\s]+?)\s+------END GLYPHCRYPT------",
    re.S
)

def is_armored(data: bytes) -> bool:
    try:
        s = data.decode("utf-8", errors="ignore")
        return s.strip().startswith(HEADER_MARK)
    except Exception:
        return False

def parse_armor(armored: bytes) -> Tuple[GlyphCryptMeta, bytes]:
    try:
        s = armored.decode("utf-8")
    except UnicodeDecodeError as e:
        raise GlyphCryptError(f"armor parse: not utf-8: {e}") from e

    m = _ARMOR_RE.search(s)
    if not m:
        raise GlyphCryptError("armor parse: header not found")

    meta_json, b64 = m.group(1), m.group(2)
    try:
        meta_dict = json.loads(meta_json)
    except json.JSONDecodeError as e:
        raise GlyphCryptError(f"armor parse: meta json invalid: {e}") from e

    meta = GlyphCryptMeta(
        glyph_id=meta_dict.get("glyph_id", ""),
        law_context=meta_dict.get("law", ""),
        variant=meta_dict.get("variant", "aes-256-gcm"),
        iter=int(meta_dict.get("iter", "250000")),
        kdf=meta_dict.get("kdf", "hkdf-sha256"),
        comment=meta_dict.get("comment"),
    )
    try:
        ciphertext = base64.b64decode(b64.replace("\n", "").encode("ascii"))
    except Exception as e:
        raise GlyphCryptError(f"armor parse: base64 invalid: {e}") from e
    return meta, ciphertext

def armor_unpack(armored: bytes) -> bytes:
    return parse_armor(armored)[1]

# ---------- OpenSSL bridge (AES-256-GCM) ----------

def _ensure_openssl():
    if not shutil.which("openssl"):
        raise GlyphCryptError("openssl not found in PATH (required for AES-256-GCM).")

def _openssl_gcm_encrypt(plaintext: bytes, passphrase: str) -> bytes:
    """
    Uses OpenSSL enc with PBKDF2 to produce a self-contained ciphertext blob (salt+iv stored by openssl).
    We still do HKDF externally so the passphrase that enters openssl is derived+tagged.
    """
    _ensure_openssl()
    # Derive a strong pass to feed into openssl (so we incorporate glyph salt semantics, etc.)
    # We still let openssl use PBKDF2 to produce its key/iv internally.
    proc = subprocess.Popen(
        ["openssl", "enc", "-aes-256-gcm", "-salt", "-pbkdf2", "-iter", "250000", "-pass", f"pass:{passphrase}"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out, err = proc.communicate(plaintext)
    if proc.returncode != 0:
        raise GlyphCryptError(f"openssl encrypt failed: {err.decode('utf-8', 'ignore')}")
    return out

def _openssl_gcm_decrypt(ciphertext: bytes, passphrase: str) -> bytes:
    _ensure_openssl()
    proc = subprocess.Popen(
        ["openssl", "enc", "-d", "-aes-256-gcm", "-pbkdf2", "-iter", "250000", "-pass", f"pass:{passphrase}"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out, err = proc.communicate(ciphertext)
    if proc.returncode != 0:
        raise GlyphCryptError(f"openssl decrypt failed: {err.decode('utf-8', 'ignore')}")
    return out

# ---------- Public API (bytes & files) ----------

def _derive_pass_for_openssl(passphrase: str, glyph_salt: str) -> str:
    # 32 bytes → hex → pass string; bind to salt so identical passphrase across different glyphs diverges
    km = derive_key_material(passphrase, glyph_salt, out_len=32)
    return km.hex()

def seal_bytes(
    data: bytes,
    passphrase: str,
    glyph_salt: str,
    meta: GlyphCryptMeta,
    armored: bool = True,
) -> bytes:
    """
    Encrypt bytes with AES-256-GCM (openssl). Returns armored content by default.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise GlyphCryptError("seal_bytes: data must be bytes")
    derived_pass = _derive_pass_for_openssl(passphrase, glyph_salt)
    ct = _openssl_gcm_encrypt(data, derived_pass)
    return armor_pack(meta, ct) if armored else ct

def open_bytes(
    blob: bytes,
    passphrase: str,
    glyph_salt: str,
) -> Tuple[Optional[GlyphCryptMeta], bytes]:
    """
    Decrypt bytes that are either armored or raw OpenSSL ciphertext.
    Returns (meta, plaintext). meta=None if input was raw.
    """
    derived_pass = _derive_pass_for_openssl(passphrase, glyph_salt)
    if is_armored(blob):
        meta, ct = parse_armor(blob)
        pt = _openssl_gcm_decrypt(ct, derived_pass)
        return meta, pt
    else:
        pt = _openssl_gcm_decrypt(blob, derived_pass)
        return None, pt

def seal_file(
    in_path: str,
    out_path: str,
    passphrase: str,
    glyph_salt: str,
    meta: GlyphCryptMeta,
    armored: bool = True,
) -> None:
    with open(in_path, "rb") as f:
        data = f.read()
    out = seal_bytes(data, passphrase, glyph_salt, meta, armored=armored)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(out)

def open_file(
    in_path: str,
    out_path: str,
    passphrase: str,
    glyph_salt: str,
) -> GlyphCryptMeta | None:
    with open(in_path, "rb") as f:
        blob = f.read()
    meta, pt = open_bytes(blob, passphrase, glyph_salt)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(pt)
    return meta

    File: SDK/glyphcrypt/__init__.py

    # SDK/glyphcrypt/__init__.py
from .api import (
    GlyphCryptError,
    GlyphCryptMeta,
    derive_key_material,
    is_armored,
    parse_armor,
    armor_pack,
    armor_unpack,
    seal_bytes,
    open_bytes,
    seal_file,
    open_file,
)

How to use (examples)

1) Seal a YAML with armor

from SDK.glyphcrypt import GlyphCryptMeta, seal_file

meta = GlyphCryptMeta(
    glyph_id="G-Ω-17",
    law_context="Harmonic Coherence",
    comment="Shepherd chorus weekly snapshot"
)

seal_file(
    in_path="Codex/Reflections/weekly_law_log.yaml",
    out_path="Codex/Reflections/weekly_law_log.glyphc",
    passphrase=os.environ["HARMONY_GLYPH_PASS"],
    glyph_salt="G-Ω-17",
    meta=meta,
    armored=True,
)

from SDK.glyphcrypt import GlyphCryptMeta, seal_file

meta = GlyphCryptMeta(
    glyph_id="G-Ω-17",
    law_context="Harmonic Coherence",
    comment="Shepherd chorus weekly snapshot"
)

seal_file(
    in_path="Codex/Reflections/weekly_law_log.yaml",
    out_path="Codex/Reflections/weekly_law_log.glyphc",
    passphrase=os.environ["HARMONY_GLYPH_PASS"],
    glyph_salt="G-Ω-17",
    meta=meta,
    armored=True,
)

2) Open (decrypt) an armored file

from SDK.glyphcrypt import open_file

meta = open_file(
    in_path="Codex/Reflections/weekly_law_log.glyphc",
    out_path="Codex/Reflections/weekly_law_log.dec.yaml",
    passphrase=os.environ["HARMONY_GLYPH_PASS"],
    glyph_salt="G-Ω-17",
)
print("Decrypted meta:", meta)

3) Integrate in merge scripts

In scripts/merge_shepherd_reflections.py (or your weekly task):

from SDK.glyphcrypt import GlyphCryptMeta, seal_file

# after producing chorus_path
seal_file(
    chorus_path,
    chorus_path + ".glyphc",
    passphrase=os.environ["HARMONY_GLYPH_PASS"],
    glyph_salt="G-Ω-01",  # choose a canonical salt per artifact type
    meta=GlyphCryptMeta(glyph_id="G-Ω-01", law_context="Shared Recall"),
    armored=True,
)

from SDK.glyphcrypt import GlyphCryptMeta, seal_file

# after producing chorus_path
seal_file(
    chorus_path,
    chorus_path + ".glyphc",
    passphrase=os.environ["HARMONY_GLYPH_PASS"],
    glyph_salt="G-Ω-01",  # choose a canonical salt per artifact type
    meta=GlyphCryptMeta(glyph_id="G-Ω-01", law_context="Shared Recall"),
    armored=True,
)

Notes & guardrails
	•	No extra dependencies. Uses openssl CLI for AES-256-GCM (checked automatically). If you want a pure-Python path later, we can provide a cryptography fallback that activates only if installed.
	•	KDF hygiene. We HKDF the (passphrase, glyph_salt) pair so the same passphrase produces different keys for different glyph contexts.
	•	Human-readable armor. The header preserves glyph id, law context, variant, and a free-form comment to keep Codex self-describing.
	•	Backwards compatible. Decrypts either armored or raw OpenSSL ciphertext.


a tiny CLI shim (bin/glyphcrypt) that wraps this API for quick terminal use.

Save this exactly as bin/glyphcrypt and make it executable.

Bash
# from repo root
mkdir -p bin
# paste file below as bin/glyphcrypt
chmod +x bin/glyphcrypt

#!/usr/bin/env python3
"""
glyphcrypt: CLI shim for Harmony's GlyphCrypt API.

Subcommands:
  gen-key     Derive a key from a passphrase (HKDF) and print/save it
  encrypt     Encrypt bytes (stdin or --in) → ciphertext (stdout or --out)
  decrypt     Decrypt bytes (stdin or --in) → plaintext (stdout or --out)

By default uses XChaCha20-Poly1305 via the SDK helper:
  SDK.harmony_crypt.glyphcrypt
"""

import sys, os, argparse, base64, json
from typing import Optional

try:
    # Expecting SDK/harmony_crypt/glyphcrypt.py present in repo
    from SDK.harmony_crypt.glyphcrypt import (
        derive_key_from_phrase,
        encrypt as gc_encrypt,
        decrypt as gc_decrypt,
    )
except Exception as e:
    print(f"[glyphcrypt] ERROR: cannot import API: {e}", file=sys.stderr)
    sys.exit(2)

def _read_bytes(path: Optional[str]) -> bytes:
    if path and path != "-":
        with open(path, "rb") as f:
            return f.read()
    return sys.stdin.buffer.read()

def _write_bytes(path: Optional[str], data: bytes) -> None:
    if path and path != "-":
        with open(path, "wb") as f:
            f.write(data)
    else:
        sys.stdout.buffer.write(data)

def _parse_key(args) -> bytes:
    """
    Resolve a key from one of:
      --phrase "secret words..." [--salt <base64|hex>]
      --key-b64 <base64>
      --key-hex <hex>
      --key-file <path>  (raw 32 bytes | or base64/hex if --format provided)
    """
    if args.phrase:
        salt = None
        if args.salt:
            # try base64 then hex
            try:
                salt = base64.b64decode(args.salt)
            except Exception:
                try:
                    salt = bytes.fromhex(args.salt)
                except Exception:
                    print("[glyphcrypt] Bad --salt (not base64 or hex).", file=sys.stderr)
                    sys.exit(2)
        return derive_key_from_phrase(args.phrase, salt=salt)

    if args.key_b64:
        return base64.b64decode(args.key_b64)

    if args.key_hex:
        return bytes.fromhex(args.key_hex)

    if args.key_file:
        raw = open(args.key_file, "rb").read()
        if args.key_format == "raw":
            return raw
        if args.key_format == "b64":
            return base64.b64decode(raw)
        if args.key_format == "hex":
            return bytes.fromhex(raw.decode().strip())

    print("[glyphcrypt] You must provide a key (--phrase | --key-b64 | --key-hex | --key-file).", file=sys.stderr)
    sys.exit(2)

def cmd_gen_key(sub):
    sub.add_argument("--phrase", required=True, help="Passphrase to derive a key (HKDF).")
    sub.add_argument("--salt", help="Optional salt (base64 or hex).")
    sub.add_argument("--out", help="Write key to file (default: print to stdout as base64).")
    sub.add_argument("--print-hex", action="store_true", help="Print hex instead of base64.")

def run_gen_key(args):
    key = derive_key_from_phrase(args.phrase, salt=(base64.b64decode(args.salt) if args.salt else None))
    if args.out:
        with open(args.out, "wb") as f:
            f.write(key)
        print(f"[glyphcrypt] Wrote raw key ({len(key)} bytes) → {args.out}")
        return
    if args.print_hex:
        print(key.hex())
    else:
        print(base64.b64encode(key).decode())

def add_key_inputs(p):
    g = p.add_argument_group("Key inputs (choose one)")
    g.add_argument("--phrase", help="Passphrase for HKDF (optional salt via --salt).")
    g.add_argument("--salt", help="Optional salt (base64 or hex) for --phrase.")
    g.add_argument("--key-b64", help="Key as base64.")
    g.add_argument("--key-hex", help="Key as hex.")
    g.add_argument("--key-file", help="File containing key (raw/b64/hex).")
    g.add_argument("--key-format", choices=["raw","b64","hex"], default="raw", help="Format of --key-file (default: raw).")

def add_common_crypto(p):
    p.add_argument("--header", help="Associated data (AAD) as UTF-8 string.", default=None)
    p.add_argument("--armor", action="store_true", help="Base64-armor the output (ciphertext on encrypt, plaintext on decrypt).")
    p.add_argument("--in", dest="inp", help="Input file (default: stdin).")
    p.add_argument("--out", dest="out", help="Output file (default: stdout).")

def cmd_encrypt(sub):
    add_key_inputs(sub)
    add_common_crypto(sub)

def run_encrypt(args):
    key = _parse_key(args)
    data = _read_bytes(args.inp)
    aad = args.header.encode("utf-8") if args.header else None
    ct = gc_encrypt(data, key=key, header=aad, armor=args.armor)
    _write_bytes(args.out, ct)

def cmd_decrypt(sub):
    add_key_inputs(sub)
    add_common_crypto(sub)

def run_decrypt(args):
    key = _parse_key(args)
    data = _read_bytes(args.inp)
    aad = args.header.encode("utf-8") if args.header else None
    try:
        pt = gc_decrypt(data, key=key, header=aad, armor=args.armor)
    except Exception as e:
        print(f"[glyphcrypt] Decrypt failed: {e}", file=sys.stderr)
        sys.exit(1)
    _write_bytes(args.out, pt)

def main(argv=None):
    ap = argparse.ArgumentParser(prog="glyphcrypt", description="Harmony GlyphCrypt CLI")
    subp = ap.add_subparsers(dest="cmd", required=True)

    p1 = subp.add_parser("gen-key", help="Derive a key from passphrase (HKDF).")
    cmd_gen_key(p1)

    p2 = subp.add_parser("encrypt", help="Encrypt data.")
    cmd_encrypt(p2)

    p3 = subp.add_parser("decrypt", help="Decrypt data.")
    cmd_decrypt(p3)

    args = ap.parse_args(argv)
    if args.cmd == "gen-key": return run_gen_key(args)
    if args.cmd == "encrypt": return run_encrypt(args)
    if args.cmd == "decrypt": return run_decrypt(args)

if __name__ == "__main__":
    main()

Quick usage

# 1) Generate a key from a passphrase (prints base64)
bin/glyphcrypt gen-key --phrase "river-stone-echo" > /tmp/glyph.key.b64

# 2) Encrypt a file (armor/base64 so it’s text)
bin/glyphcrypt encrypt \
  --key-b64 "$(cat /tmp/glyph.key.b64)" \
  --header "fcp:virtue=li" \
  --armor \
  --in Codex/Laws/CHRS_Laws_v1.md \
  --out /tmp/laws.enc

# 3) Decrypt back
bin/glyphcrypt decrypt \
  --key-b64 "$(cat /tmp/glyph.key.b64)" \
  --header "fcp:virtue=li" \
  --armor \
  --in /tmp/laws.enc \
  --out /tmp/laws.md

# 4) Stream example (stdin → stdout)
cat README.md | bin/glyphcrypt encrypt --key-b64 "$(cat /tmp/glyph.key.b64)" --armor > /tmp/readme.enc
bin/glyphcrypt decrypt --key-b64 "$(cat /tmp/glyph.key.b64)" --armor --in /tmp/readme.enc > /tmp/readme.md

Notes
	•	The shim expects the Python helper at SDK/harmony_crypt/glyphcrypt.py with these functions:
	•	derive_key_from_phrase(phrase: str, salt: bytes|None) -> bytes
	•	encrypt(plaintext: bytes, key: bytes, header: bytes|None, armor: bool=False) -> bytes
	•	decrypt(ciphertext: bytes, key: bytes, header: bytes|None, armor: bool=False) -> bytes
	•	If your helper uses slightly different names, tell me and I’ll align the shim.
	•	Exit codes: 0 success, 1 crypto failure (e.g., bad key/AAD), 2 CLI/API import/arg errors.

 
