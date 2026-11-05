# AetherOS

> **One OS. Every App. AI Native.**

A universal AI operating system capable of running **Linux**, **Android**, **Windows/.NET**, **OCI Containers**, and **AI agents** through a single unified interface.

Instead of writing a kernel from scratch, AetherOS uses the battle-tested **Linux kernel** as the hardware abstraction layer and structures all runtimes, compatibility layers, and AI capabilities into modular, sandboxed subsystems orchestrated over a system-wide **Model Context Protocol (MCP)** bus.

---

## 🏛️ System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │                AetherOS Shell                │
                    │          (Rust + Flutter + Wayland)          │
                    └──────────────────────┬───────────────────────┘
                                           │
                     ┌─────────────────────┼─────────────────────┐
                     │                     │                     │
                     ▼                     ▼                     ▼
             ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
             │   Aether AI   │     │  Application  │     │ System Daemon │
             │  Runtime Core │     │      Hub      │     │  & Telemetry  │
             └───────┬───────┘     └───────┬───────┘     └───────┬───────┘
                     │                     │                     │
                     └─────────────────────┼─────────────────────┘
                                           │
                                           ▼
                             ┌───────────────────────────┐
                             │       AetherMCP Bus       │
                             │  (IPC / Unix Socket / RPC)│
                             └─────────────┬─────────────┘
                                           │
      ┌───────────────────┬────────────────┼───────────────────┬───────────────────┐
      ▼                   ▼                ▼                   ▼                   ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Linux Native  │ │    Android    │ │  .NET CoreCLR │ │ Windows/Wine  │ │  OCI & K3s    │
│  ELF / Flatpak│ │    Waydroid   │ │  MAUI / Avln  │ │ Proton / DXVK │ │  Containers   │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │                 │                 │
        └─────────────────┴─────────────────┼─────────────────┴─────────────────┘
                                            ▼
                      ┌───────────────────────────────────────────┐
                      │               Linux Kernel                │
                      │ (Namespaces, cgroups v2, eBPF, Seccomp)   │
                      └───────────────────────────────────────────┘
```

---

## 🚀 Key Innovations

### 1. Multi-Runtime Execution Layer
| Application Ecosystem | Subsystem Technology | How It Works |
| :--- | :--- | :--- |
| **Linux Native** | ELF / Flatpak / AppImage | Native execution with Seccomp & namespace isolation |
| **Android** | Waydroid + Binder IPC | Direct AOSP container with PipeWire audio and Wayland GPU passthrough |
| **.NET / Windows** | CoreCLR / Avalonia / MAUI | Native execution of `.dll`, `.exe`, and cross-platform desktop UI |
| **Windows Legacy & Games**| Wine / Proton / DXVK / VKD3D | DirectX to Vulkan translation with zero user configuration |
| **Containers & K8s** | containerd + k3s | Built-in local Kubernetes cluster and OCI container engine |

### 2. Native Model Context Protocol (MCP) Bus
Instead of bolting on AI after the fact, AetherOS provides **`aether-mcpd`**, a kernel/system-level daemon exposing OS functions as structured tools. AI agents (local via llama.cpp or cloud-based) can:
- Query hardware telemetry (`os_system_status`)
- Autonomously resolve and install software (`os_package_install`)
- Launch sandboxed applications (`os_app_launch`)
- Trigger multi-app automations (`os_automate`)

### 3. Universal Package Manager (`aether install`)
No more deciding between `pacman`, `apt`, `flatpak`, `snap`, `docker`, or `apk`. The `aether` resolver determines the optimal runtime based on security and desktop integration:
```bash
# Sandboxed Flatpak with Wayland integration
aether install vscode

# Android APK routed to Waydroid container
aether install com.spotify.music.apk

# Windows executable configured with Proton prefix
aether install setup.exe

# OCI container fetched and registered
aether install docker://redis:alpine
```

---

## 📦 Project Structure

```
at-os/
├── Cargo.toml                    # Rust workspace manifest
├── crates/
│   ├── aether-core/              # Core types, IPC models, telemetry & MCP schemas
│   ├── aether-runtime/           # Multi-subsystem launcher (Waydroid, .NET, Wine, OCI)
│   ├── aether-pkg/               # Universal package manager resolver
│   ├── aether-mcpd/              # System-wide MCP daemon (JSON-RPC over Unix socket)
│   └── aether-cli/               # Unified 'aether' command line interface
├── docs/
│   ├── ARCHITECTURE.md           # Full system architecture specification
│   ├── RUNTIMES.md               # Detailed runtime execution specs
│   └── MCP_BUS.md                # MCP system daemon specification
├── scripts/
│   ├── run_demo.sh               # Live demonstration of AetherOS core capabilities
│   └── bootstrap_arch_base.sh    # Arch Linux rootfs bootstrap recipe
└── examples/
    └── mcp_tool_manifest.json    # Sample app MCP tool declaration
```

---

## ⚡ Quickstart

### Prerequisites
- Linux kernel 6.x or newer (Ubuntu, Arch, Debian, Fedora)
- Rust 1.75+ & Cargo

### Build and Run
```bash
# Clone and enter workspace
cd at-os

# Build all workspace crates
cargo build --release

# Run the live demonstration
./scripts/run_demo.sh
```

### Using the `aether` CLI

```bash
# 1. Check subsystem readiness
./target/release/aether status

# 2. Universal install with AI dry-run preview
./target/release/aether install vscode --dry-run
./target/release/aether install app.apk --dry-run

# 3. Direct multi-runtime execution
./target/release/aether run app.apk
./target/release/aether run app.dll
./target/release/aether run game.exe

# 4. Query MCP System Bus tools
./target/release/aether mcp tools

# 5. Natural Language AI Assistant
./target/release/aether ai "Show system health status"
./target/release/aether ai "Install vscode and run redis container"
```

---

## 🗺️ Roadmap

- **Phase 1: Base Core (Current)**
  - [x] Multi-runtime detection & orchestrator (`aether-runtime`)
  - [x] Universal package resolver (`aether-pkg`)
  - [x] System MCP Daemon (`aether-mcpd`)
  - [x] Unified CLI controller (`aether`)
  - [x] Arch Linux base bootstrap recipes
- **Phase 2: Desktop Shell & AI Runtime**
  - [ ] Rust/Wayland custom compositor bridge (`aether-shell`)
  - [ ] Flutter-based AI HUD & desktop overlay
  - [ ] Local model manager (GGUF quantizer & runner with llama.cpp)
  - [ ] Android notification and window lifecycle sync
- **Phase 3: Universal Platform**
  - [ ] Developer SDK & App Store
  - [ ] Zero-trust eBPF security sandboxing
  - [ ] Cloud sync and hybrid workstation orchestration

---

## 📄 License
Licensed under Apache 2.0.
