# AetherOS: AI-Native Operating System (Arch Linux + Hyprland)

**AetherOS** is an AI-Native 64-bit operating system combining a modern **Arch Linux** base with the **Hyprland** Wayland compositor, a clean macOS / iOS frosted glass aesthetic, and the **Kernel Model Context Protocol (MCP) Daemon & SLM Intelligence Core**.

---

## 🌟 Highlights

- **Hyprland Wayland Desktop**: 12px rounded corners, dual-pass frosted glass blur, fluid spring animations, and subtle gradient borders.
- **macOS Top Menu Bar (Waybar)**: Frosted glass status bar with active workspaces, system clock, CPU & RAM gauges, and an **AI Copilot** indicator.
- **Spotlight App Launcher (Wofi)**: Centered modern search launcher triggered by `Super + Space`.
- **Aether MCP Daemon (`aether-mcpd`)**: Exposes system internals, threads, PSI pressure metrics, and cgroups to local SLM agents and user tools over Unix sockets (`/run/aether/mcp.sock`) and HTTP (`:9090`).
- **AI Copilot CLI (`aetherctl`)**: Conversational interface for diagnosing system health, tuning thread latency, and compacting kernel memory.
- **Virtual Machine Manager Ready**: Pre-configured as a libvirt domain (`AetherOS-Mini`) running on KVM.
- **Physical Bare-Metal Bootable**: Write `aetheros-mini.img` directly to any USB drive using `dd` to boot on physical PC hardware.

---

## ⌨️ Hyprland Keybindings

- `Super` + `Enter`: Open terminal (`foot`)
- `Super` + `Space`: Spotlight app launcher (`wofi`)
- `Super` + `A`: Open **Aether AI Copilot** diagnostic window
- `Super` + `C`: Run kernel memory compaction (`aetherctl compact`)
- `Super` + `T`: Inspect active threads (`aetherctl threads`)
- `Super` + `Q`: Close active window
- `Super` + `V`: Toggle window floating mode
- `Super` + `F`: Toggle fullscreen
- `Super` + `1` .. `5`: Switch workspaces

---

## 🚀 Running & Testing

### 1. View in Virtual Machine Manager GUI
Launch Virt-Manager:
```bash
virt-manager
```
Double-click `AetherOS-Mini` in the list to open the display console.

Or launch the dedicated viewer window directly:
```bash
virt-viewer --connect qemu:///system AetherOS-Mini
```

### 2. Boot on Physical PC Hardware via USB
```bash
sudo dd if=aetheros-mini.img of=/dev/sdX bs=4M status=progress conv=fsync
```
