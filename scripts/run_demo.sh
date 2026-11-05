#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$DIR/target/debug/aether"

echo "=== AetherOS Live Demonstration ==="
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
"$DIR/target/release/aether-ai" --models
echo

# 6. Aether AI Interface
echo ">> Testing Natural Language OS AI Interface:"
"$BIN" ai "Show system health status"
echo
"$BIN" ai "Install com.spotify.music.apk"
echo

# 7. Aether Shell Telemetry
echo ">> Testing Aether Shell IPC Telemetry Bridge:"
"$DIR/target/release/aether-ai" "Show system status across all runtimes"
echo

echo "=== Demonstration Completed Successfully ==="
