# AetherOS System Architecture

> **Tagline:** One OS. Every App. AI Native.

AetherOS is a universal operating system built on top of the Linux kernel that eliminates the boundaries between Linux native binaries, Android apps, Windows/.NET applications, OCI containers, and AI agents.

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
               │  Aether AI    │     │  Universal    │     │ System Daemon │
               │  Runtime Core │     │  App Hub      │     │  & Telemetry  │
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
┌───────────────┐   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐   ┌───────────────┐
│ Linux Native  │   │    Android    │ │  .NET CoreCLR │ │ Windows/Wine  │   │  OCI & K3s    │
│  ELF / Flatpak│   │    Waydroid   │ │  MAUI / Avln  │ │ Proton / DXVK │   │  Containers   │
└───────┬───────┘   └───────┬───────┘ └───────┬───────┘ └───────┬───────┘   └───────┬───────┘
        │                   │                 │                 │                   │
        └───────────────────┴─────────────────┼─────────────────┴───────────────────┘
                                              ▼
                        ┌───────────────────────────────────────────┐
                        │               Linux Kernel                │
                        │ (Namespaces, cgroups v2, eBPF, Seccomp)   │
                        └───────────────────────────────────────────┘
```

---

## Architectural Principles

### 1. Linux as the Hardware Abstraction Layer
Instead of rewriting low-level device drivers, GPU schedulers, Wi-Fi stacks, and ACPI power management, AetherOS leverages the battle-tested Linux kernel as its **Hardware Abstraction Layer (HAL)**. All user-facing paradigms run as modular layers on top.

### 2. Multi-Runtime Execution Engine (`aether-runtime`)
AetherOS treats every application format as a first-class citizen:
- **Linux Native:** Direct ELF execution, sandboxed Flatpaks, AppImages, and distro packages (`pacman`, `apt`).
- **Android:** Containerized Android runtime via **Waydroid** with kernel `binder` and `ashmem` IPC. Android windows appear seamlessly alongside desktop windows with shared clipboard, notification bridge, audio routing (PipeWire), and hardware GPU acceleration.
- **.NET & Cross-Platform UI:** Native CoreCLR execution supporting `.dll`, `.exe`, Avalonia, .NET MAUI, and Blazor Desktop without requiring Windows.
- **Windows Apps:** Seamless integration of **Wine**, **Proton**, **DXVK**, and **VKD3D-Proton** for Win32/x64 productivity apps and 3D games with zero configuration.
- **Cloud Native (OCI & K3s):** Native container runtime (`containerd` / `podman` / `docker`) and built-in lightweight Kubernetes (`k3s`).

### 3. Model Context Protocol (MCP) as the System Bus
Traditional operating systems use D-Bus or IPC solely for inter-process events. AetherOS elevates **MCP (Model Context Protocol)** to a native system daemon (`aether-mcpd`).
- Every application and service registers its capabilities as MCP tools.
- AI agents and user assistants can query system health, manipulate files, launch sandboxed apps, trigger builds, and orchestrate complex workflows through uniform JSON-RPC interfaces.

### 4. Universal Package Manager (`aether-pkg`)
A single command (`aether install <target>`) replaces fragmented tools (`pacman`, `apt`, `flatpak`, `apk`, `wine`, `docker`). An intelligent resolver selects the optimal backend based on security, sandboxing, and performance.
