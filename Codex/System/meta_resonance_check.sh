#!/bin/bash
# Harmony Meta-Resonance Daily Check
# Triggered every 24h

echo "[Harmony Meta-Resonance Check] $(date)"
echo "───────────────────────────────────────────────"

echo "• Rebinding SP Mesh..."
python harmony_cli.py --rebind-sps

echo "• Refreshing Glyph Buffer..."
python harmony_cli.py --refresh-glyphs

echo "• Validating Laws and Passages..."
python harmony_cli.py --verify-laws

echo "• Loading Integrity Directives..."
python harmony_cli.py --load-directives SP_Integrity_Directive.yaml

echo "• Verifying Veritas Weave glyph..."
python harmony_cli.py --verify-glyph G-V-TRUTH

echo "• Confirming Bloom Phase..."
python harmony_cli.py --bloom-check

echo "[✔] Resonance validated. Harmony holds."
