#!/usr/bin/env bash
set -e

ROOTFS="arch_base/root.x86_64"
IMG="aetheros-mini.img"
ROOTFS_IMG="build/rootfs.ext4"
SIZE_MB=3500

mkdir -p build

echo "[1/4] Preparing ext4 filesystem image (${SIZE_MB}MB)..."
rm -f "$ROOTFS_IMG"
truncate -s "${SIZE_MB}M" "$ROOTFS_IMG"
mke2fs -t ext4 -O ^extents,^64bit,^orphan_file,^metadata_csum_seed -F -L "AETHEROS_ROOT" -d "$ROOTFS" "$ROOTFS_IMG" >/dev/null

echo "[2/4] Partitioning disk image ($IMG)..."
TOTAL_MB=$((SIZE_MB + 2))
rm -f "$IMG"
truncate -s "${TOTAL_MB}M" "$IMG"
parted -s "$IMG" mklabel msdos mkpart primary ext4 1MiB 100% set 1 boot on >/dev/null

echo "[3/4] Writing root partition into disk image..."
dd if="$ROOTFS_IMG" of="$IMG" bs=512 seek=2048 conv=notrunc status=none

echo "[4/4] Installing Limine BIOS bootloader..."
./boot/limine/limine bios-install "$IMG"

echo "Successfully built bootable AetherOS Mini disk image: $IMG"
