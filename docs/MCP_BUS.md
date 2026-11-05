# AetherOS System MCP Bus (`aether-mcpd`)

## What is the MCP Bus?

In traditional operating systems, applications communicate via D-Bus (Linux), COM/WinRT (Windows), or XPC (macOS). These protocols are designed for deterministic function calls between compiled binaries, with zero comprehension of semantics, goals, or AI agents.

**AetherOS replaces the paradigm with the Model Context Protocol (MCP) as a native System Bus.**

Every subsystem, system service, hardware monitor, and desktop application registers itself with `aether-mcpd`. Local LLMs (via llama.cpp/Ollama) or cloud models interact with the OS by inspecting tools, reading context, and dispatching structured actions.

```
┌────────────────────────────────────────────────────────┐
│             Aether AI Assistant / Agent                │
└───────────────────────────┬────────────────────────────┘
                            │ JSON-RPC 2.0 (MCP Protocol)
                            ▼
┌────────────────────────────────────────────────────────┐
│             aether-mcpd System Daemon                  │
│       (Listening on /run/user/$UID/aether-mcp.sock)    │
└──────┬───────────────┬────────────────┬──────────────┬─┘
       │               │                │              │
       ▼               ▼                ▼              ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│  OS System   ││  Universal   ││ Application  ││  Universal   │
│  Diagnostics ││  Package Mgr ││  Lifecycle   ││  Automation  │
└──────────────┘└──────────────┘└──────────────┘└──────────────┘
```

---

## Standard MCP Tools Exposed by AetherOS

### 1. `os_system_status`
Queries hardware metrics, GPU status (NVIDIA NVML / AMD ROCm), kernel details, and the readiness of Waydroid, .NET, Wine, Docker, and K3s.

### 2. `os_package_install`
Intelligently resolves and installs any software target across Flatpak, Android APK, .NET global tool, Wine bottle, OCI container image, or native package.

### 3. `os_app_launch`
Launches any application target through its appropriate runtime sandbox.

### 4. `os_automate`
Executes multi-step automation pipelines (download, rename, OCR, database sync, notify).

---

## Direct Integration Example

An AI agent or desktop shortcut can connect directly to the Aether MCP daemon:

```bash
# Start or query the MCP daemon
aether mcp tools

# Execute tool call
aether mcp call os_package_install '{"target": "vscode", "dry_run": true}'
```
