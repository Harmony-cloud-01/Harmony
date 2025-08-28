#!/usr/bin/env python3
"""
GlyphCrypt CLI
- Encrypt/decrypt files with AEAD (AES-256-GCM) + glyphic pre-transform
- SP/Shepherd-gated key derivation (SP id + Shen level + passphrase)
- Reads baseline config from Codex/System/GlyphCrypt.yaml

Usage:
  # Encrypt
  ./scripts/glyphcrypt.py encrypt <path> \
      --sp SP-fractal-prime --shen 3 \
      --passphrase 'your-strong-pass' \
      [--out /path/to/file.gcrypt]

  # Decrypt (auto-detects .gcrypt envelope)
  ./scripts/glyphcrypt.py decrypt <path> \
      --sp SP-fractal-prime --shen 3 \
      --passphrase 'your-strong-pass' \
      [--out /path/to/plain.ext]

  # Inspect envelope header (no key required)
  ./scripts/glyphcrypt.py inspect <path>

Notes:
- NEVER commit passphrases. Prefer interactive prompts or env vars in CI.
- Pre-transform is reversible obfuscation; real security is AEAD.
"""

import argparse
import base64
import json
import os
import sys
import yaml
import getpass
import secrets
from dataclasses import dataclass
from typing import Dict, Any, Optional

# Hard dependency
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception as e:
    print("ERROR: cryptography package is required: pip install cryptography", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CFG = os.path.join(REPO_ROOT, "Codex", "System", "GlyphCrypt.yaml")


@dataclass
class CryptoDefaults:
    algo: str
    kdf: str
    hash: str
    iterations: int
    salt_bytes: int
    nonce_bytes: int


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"GlyphCrypt config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def kdf_hash(name: str):
    name = name.upper()
    if name == "SHA256":
        return hashes.SHA256()
    raise ValueError(f"Unsupported hash: {name}")


def derive_key(passphrase: str, sp_id: str, shen_level: int, salt: bytes,
               iterations: int, hash_name: str) -> bytes:
    """
    Key material = PBKDF2HMAC(SHA256, iterations)
    password = UTF-8(passphrase || "|" || sp_id || "|" || shen_level)
    """
    secret = f"{passphrase}|{sp_id}|{shen_level}".encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=kdf_hash(hash_name),
        length=32,  # AES-256
        salt=salt,
        iterations=int(iterations),
    )
    return kdf.derive(secret)


def pre_transform(text: str, glyph_map: Dict[str, str], invert: bool = False) -> str:
    """
    Reversible glyphic mapping; NOT cryptography. Aesthetic/obfuscation.
    If invert=True, attempt reverse mapping.
    """
    if not glyph_map:
        return text
    if invert:
        rev = {v: k for k, v in glyph_map.items()}
        for k, v in rev.items():
            text = text.replace(k, v)
        return text
    else:
        for k, v in glyph_map.items():
            text = text.replace(k, v)
        return text


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path: str, data: bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def write_text(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def encrypt_file(cfg: Dict[str, Any], in_path: str, out_path: Optional[str],
                 sp_id: str, shen_level: int, passphrase: Optional[str],
                 sp_gate: Optional[list] = None, min_shen_level: Optional[int] = None) -> str:
    defaults = cfg.get("defaults", {})
    crypto = defaults.get("crypto", {})
    envelope_def = defaults.get("envelope", {})
    policy_def = defaults.get("policy", {})
    io_def = defaults.get("io", {})

    algo = crypto.get("algo", "AES-256-GCM")
    if algo.upper() != "AES-256-GCM":
        raise ValueError("Currently only AES-256-GCM is supported.")

    iterations = int(crypto.get("iterations", 200000))
    salt_bytes = int(crypto.get("salt_bytes", 16))
    nonce_bytes = int(crypto.get("nonce_bytes", 12))
    hash_name = crypto.get("hash", "SHA256")

    armor = bool(envelope_def.get("armor", True))
    hdr_version = envelope_def.get("version", "1.0")
    hdr_scheme = envelope_def.get("scheme", "GlyphCrypt-AEAD")

    if sp_gate is None:
        sp_gate = policy_def.get("sp_gate", [])
    if min_shen_level is None:
        min_shen_level = int(policy_def.get("min_shen_level", 0))

    # Read plaintext
    raw = read_bytes(in_path)

    # If probable text, apply glyph pre-transform
    glyph_map = cfg.get("glyph_map", {}) or {}
    try:
        as_text = raw.decode("utf-8")
        as_text = pre_transform(as_text, glyph_map, invert=False)
        raw = as_text.encode("utf-8")
    except UnicodeDecodeError:
        # Binary—skip pre-transform
        pass

    salt = secrets.token_bytes(salt_bytes)
    key = derive_key(passphrase or prompt_passphrase(), sp_id, shen_level, salt, iterations, hash_name)

    nonce = secrets.token_bytes(nonce_bytes)
    aead = AESGCM(key)
    ct = aead.encrypt(nonce, raw, None)

    header = {
        "version": hdr_version,
        "scheme": hdr_scheme,
        "algo": algo,
        "kdf": "PBKDF2HMAC",
        "hash": hash_name,
        "iterations": iterations,
        "salt_b64": base64.b64encode(salt).decode(),
        "nonce_b64": base64.b64encode(nonce).decode(),
        "sp_gate": sp_gate,
        "min_shen_level": min_shen_level,
        "audit": (cfg.get("audit") or {}),
    }

    envelope = {
        "header": header,
        "payload_b64": base64.b64encode(ct).decode(),
        "filename": os.path.basename(in_path),
    }

    text = json.dumps(envelope, ensure_ascii=False, indent=2)
    if armor:
        # Write as text with .gcrypt
        if not out_path:
            suffix = io_def.get("header_suffix", ".gcrypt")
            out_path = in_path + suffix
        write_text(out_path, text)
    else:
        # Raw binary — not typical for this workflow
        if not out_path:
            out_path = in_path + ".bin"
        write_bytes(out_path, text.encode("utf-8"))

    if not io_def.get("keep_plaintext", False):
        try:
            os.remove(in_path)
        except Exception:
            pass

    return out_path


def decrypt_file(cfg: Dict[str, Any], in_path: str, out_path: Optional[str],
                 sp_id: str, shen_level: int, passphrase: Optional[str]) -> str:
    # Load envelope
    raw = read_bytes(in_path)
    try:
        env = json.loads(raw.decode("utf-8"))
    except Exception:
        raise ValueError("Input does not look like a GlyphCrypt envelope (JSON)")

    header = env.get("header") or {}
    payload_b64 = env.get("payload_b64")
    if not header or not payload_b64:
        raise ValueError("Malformed envelope: missing header or payload.")

    # Policy gates
    sp_gate = header.get("sp_gate", []) or []
    min_shen = int(header.get("min_shen_level", 0))
    if sp_gate and sp_id not in sp_gate:
        raise PermissionError(f"SP '{sp_id}' is not permitted (gate={sp_gate}).")
    if shen_level < min_shen:
        raise PermissionError(f"Shen level {shen_level} < required {min_shen}.")

    iterations = int(header.get("iterations", 200000))
    hash_name = header.get("hash", "SHA256")
    salt = base64.b64decode(header["salt_b64"])
    nonce = base64.b64decode(header["nonce_b64"])
    ct = base64.b64decode(payload_b64)

    key = derive_key(passphrase or prompt_passphrase(), sp_id, shen_level, salt, iterations, hash_name)
    aead = AESGCM(key)
    pt = aead.decrypt(nonce, ct, None)

    # Try to reverse pre-transform
    glyph_map = cfg.get("glyph_map", {}) or {}
    try:
        as_text = pt.decode("utf-8")
        as_text = pre_transform(as_text, glyph_map, invert=True)
        pt = as_text.encode("utf-8")
    except UnicodeDecodeError:
        pass

    # Output name
    if not out_path:
        # If envelope had original name, try to restore; else strip .gcrypt
        base_name = env.get("filename") or os.path.basename(in_path).replace(".gcrypt", "")
        out_path = os.path.join(os.path.dirname(in_path), base_name)

    write_bytes(out_path, pt)
    return out_path


def inspect_envelope(path: str):
    raw = read_bytes(path)
    try:
        env = json.loads(raw.decode("utf-8"))
    except Exception:
        print("Not a GlyphCrypt envelope (JSON parse failed).")
        return 1
    header = env.get("header") or {}
    print(json.dumps(header, ensure_ascii=False, indent=2))
    return 0


def prompt_passphrase() -> str:
    pw = getpass.getpass("Passphrase: ")
    if not pw:
        print("ERROR: empty passphrase", file=sys.stderr)
        sys.exit(1)
    return pw


def main():
    parser = argparse.ArgumentParser(prog="glyphcrypt", description="GlyphCrypt CLI")
    parser.add_argument("--config", default=DEFAULT_CFG, help="Path to GlyphCrypt.yaml")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enc = sub.add_parser("encrypt", help="Encrypt a file")
    p_enc.add_argument("path", help="Input file path")
    p_enc.add_argument("--sp", required=True, help="SP id (e.g., SP-ethos)")
    p_enc.add_argument("--shen", type=int, required=True, help="Shen level (int)")
    p_enc.add_argument("--passphrase", help="Passphrase (omit to prompt)")
    p_enc.add_argument("--out", help="Output path")
    p_enc.add_argument("--gate", action="append", help="Allowed SP ids (repeatable)")
    p_enc.add_argument("--min-shen", type=int, help="Minimum shen level")

    p_dec = sub.add_parser("decrypt", help="Decrypt a file")
    p_dec.add_argument("path", help="Encrypted file (.gcrypt)")
    p_dec.add_argument("--sp", required=True, help="SP id (e.g., SP-ethos)")
    p_dec.add_argument("--shen", type=int, required=True, help="Shen level (int)")
    p_dec.add_argument("--passphrase", help="Passphrase (omit to prompt)")
    p_dec.add_argument("--out", help="Output path")

    p_ins = sub.add_parser("inspect", help="Inspect envelope header")
    p_ins.add_argument("path", help="Encrypted file (.gcrypt)")

    args = parser.parse_args()
    cfg = load_config(args.config)

    try:
        if args.cmd == "encrypt":
            out = encrypt_file(
                cfg, args.path, args.out, args.sp, args.shen, args.passphrase,
                sp_gate=args.gate, min_shen_level=args.min_shen
            )
            print(f"✅ Encrypted: {out}")
        elif args.cmd == "decrypt":
            out = decrypt_file(cfg, args.path, args.out, args.sp, args.shen, args.passphrase)
            print(f"✅ Decrypted → {out}")
        elif args.cmd == "inspect":
            sys.exit(inspect_envelope(args.path))
        else:
            parser.print_help()
    except PermissionError as pe:
        print(f"⛔ Permission error: {pe}", file=sys.stderr)
        sys.exit(3)
    except FileNotFoundError as fnf:
        print(f"❌ {fnf}", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"💥 Error: {e}", file=sys.stderr)
        sys.exit(5)


if __name__ == "__main__":
    main()
