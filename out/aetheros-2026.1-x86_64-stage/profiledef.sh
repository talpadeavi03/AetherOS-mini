#!/usr/bin/env bash
# ==============================================================================
# AetherOS Archiso Profile Definition
# ==============================================================================

iso_name="aetheros"
iso_label="AETHER_$(date +%Y%m)"
iso_publisher="AetherOS Core Foundation <https://aetheros.org>"
iso_application="AetherOS Live / Installation ISO"
iso_version="2026.1-alpha"
install_dir="arch"
buildmodes=('iso')
bootmodes=(
    'bios.syslinux.mbr'
    'bios.syslinux.eltorito'
    'uefi-x64.systemd-boot.esp'
    'uefi-x64.systemd-boot.eltorito'
)
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '15')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/etc/sudoers.d"]="0:0:750"
  ["/root"]="0:0:750"
  ["/usr/local/bin/aether"]="0:0:755"
  ["/usr/local/bin/aether-mcpd"]="0:0:755"
  ["/usr/local/bin/aether-shell"]="0:0:755"
  ["/usr/local/bin/aether-ai"]="0:0:755"
  ["/etc/systemd/system/aether-mcpd.service"]="0:0:644"
  ["/etc/systemd/system/aether-shell.service"]="0:0:644"
)
