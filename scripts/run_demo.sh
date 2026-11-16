#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Auto-detect release or debug binaries
if [ -f "$DIR/target/release/aether" ]; then
    BIN="$DIR/target/release/aether"
elif [ -f "$DIR/target/debug/aether" ]; then
    BIN="$DIR/target/debug/aether"
else
    echo ">> Aether binary not found. Building release binary..."
    cargo build --release --manifest-path "$DIR/Cargo.toml"
    BIN="$DIR/target/release/aether"
fi

if [ -f "$DIR/target/release/aether-ai" ]; then
    AI_BIN="$DIR/target/release/aether-ai"
elif [ -f "$DIR/target/debug/aether-ai" ]; then
    AI_BIN="$DIR/target/debug/aether-ai"
else
    AI_BIN="$BIN" # fallback
fi

echo "=== AetherOS Live Demonstration ==="
echo "Using binary: $BIN"
echo

# 1. System Info & Architecture
"$BIN" info
echo

# 2. Subsystem Matrix
"$BIN" status
echo

# 3. Universal Package Manager Resolution
echo ">> Testing Universal Package Resolution: 'vscode' (Flatpak sandbox)"
"$BIN" install vscode --dry-run
echo

echo ">> Testing Universal Package Resolution: 'com.spotify.music.apk' (Android Waydroid)"
"$BIN" install com.spotify.music.apk --dry-run
echo

echo ">> Testing Universal Package Resolution: 'setup.exe' (Windows / Wine Proton)"
"$BIN" install setup.exe --dry-run
echo

echo ">> Testing Universal Package Resolution: 'docker://redis:alpine' (OCI Container Engine)"
"$BIN" install docker://redis:alpine --dry-run
echo

# 4. MCP Bus Tools
echo ">> Querying AetherOS MCP System Tools:"
"$BIN" mcp tools
echo

# 5. Local Model Engine & Quantization Profiles
echo ">> Querying AetherOS Local Model Catalog & Quantization Profiles:"
"$AI_BIN" --models
echo

# 6. Aether AI Interface
echo ">> Testing Natural Language OS AI Interface:"
"$BIN" ai "Show system health status"
echo
"$BIN" ai "Install com.spotify.music.apk"
echo

# 7. Aether Shell Telemetry
echo ">> Testing Aether Shell IPC Telemetry Bridge:"
"$AI_BIN" "Show system status across all runtimes"
echo

echo "=== Demonstration Completed Successfully ==="
