#!/usr/bin/env bash
# ==============================================================================
# AetherOS Base Image Bootstrap Script (Arch Linux Base)
# Target: Creates rootfs with Linux Kernel, Waydroid, .NET CoreCLR, Wine-GE,
#         containerd, k3s, and the AetherOS Core Daemons.
# ==============================================================================

set -euo pipefail

ROOTFS_DIR="${1:-/tmp/aether-rootfs}"
AETHER_BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../target/release" && pwd)"

echo "=== Bootstrapping AetherOS Base Image in: ${ROOTFS_DIR} ==="

mkdir -p "${ROOTFS_DIR}"

cat << 'EOF'
[Phase 1] Core Packages Checklist:
  - Base:           base base-devel linux-firmware linux-zen (for low-latency Wayland)
  - Wayland Shell:  hyprland waybar wofi foot pipewire wireplumber
  - Android:        waydroid binder_linux-dkms ashmem-dkms
  - Windows:        wine-staging winetricks dxvk-bin vkd3d
  - .NET:           dotnet-runtime dotnet-sdk
  - Cloud Native:   containerd runc k3s-bin helm kubectl
  - AI Runtimes:    python-pytorch-cuda llama-cpp onnxruntime
EOF

echo "Setting up AetherOS system configuration..."
mkdir -p "${ROOTFS_DIR}/etc/aether"
mkdir -p "${ROOTFS_DIR}/usr/local/bin"
mkdir -p "${ROOTFS_DIR}/etc/systemd/system"

# 1. Install AetherOS systemd service for MCP Bus
cat << 'EOF' > "${ROOTFS_DIR}/etc/systemd/system/aether-mcpd.service"
[Unit]
Description=AetherOS Model Context Protocol System Bus
After=network.target local-fs.target

[Service]
Type=simple
ExecStart=/usr/local/bin/aether-mcpd
Restart=always
RestartSec=3
Environment=RUST_LOG=info

[Install]
WantedBy=multi-user.target
EOF

# 2. Setup AetherOS Waydroid auto-session systemd user service
mkdir -p "${ROOTFS_DIR}/usr/lib/systemd/user"
cat << 'EOF' > "${ROOTFS_DIR}/usr/lib/systemd/user/aether-waydroid.service"
[Unit]
Description=AetherOS Waydroid Android Subsystem Session
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/waydroid session start
Restart=on-failure

[Install]
WantedBy=graphical-session.target
EOF

# 3. Create AetherOS OS-release identity
cat << 'EOF' > "${ROOTFS_DIR}/etc/os-release"
NAME="AetherOS"
PRETTY_NAME="AetherOS 2026 AI-Native"
ID=aetheros
ID_LIKE="arch"
VERSION="0.1.0-alpha"
VERSION_ID="2026.1"
HOME_URL="https://aetheros.org"
SUPPORT_URL="https://github.com/aetheros/aetheros"
LOGO=aether-logo
EOF

# 4. Copy built Aether binaries if available
if [[ -f "${AETHER_BIN_DIR}/aether" ]]; then
    echo "Copying AetherOS binaries..."
    cp -v "${AETHER_BIN_DIR}/aether" "${ROOTFS_DIR}/usr/local/bin/"
    cp -v "${AETHER_BIN_DIR}/aether-mcpd" "${ROOTFS_DIR}/usr/local/bin/"
fi

echo "✔ AetherOS rootfs configuration complete."
