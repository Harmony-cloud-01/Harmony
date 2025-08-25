#!/bin/bash

echo "🔍 Harmony System Status Check — $(date)"

# 1. PostgreSQL service
echo -n "🛢️ PostgreSQL: "
pg_isready

# 2. Virtual environment
echo "🐍 Python Virtual Env:"
echo "  VIRTUAL_ENV=$VIRTUAL_ENV"
echo "  Python: $(which python)"

# 3. Harmony CLI
echo -n "🛠️ Harmony CLI: "
command -v harmony || echo "❌ CLI not found in PATH"

# 4. Backup Archive
echo "💾 Backup Archive in /Volumes/harmony/archive:"
ls -lh /Volumes/harmony/archive 2>/dev/null || echo "❌ Not found"

# 5. MMSI modules
echo "🎙️ MMSI Modules:"
ls -1 ~/Projects/Harmony/MMSI/modules/*.py 2>/dev/null || echo "❌ MMSI modules missing"

# 6. Mesh & SP index
echo "🧬 Meshes:"
ls -1 ~/Projects/Harmony/Codex/Meshes/*.yaml 2>/dev/null

echo "🌀 SPs:"
ls -1 ~/Projects/Harmony/Codex/SPs/*.yaml 2>/dev/null

echo "✅ Harmony status check complete."
