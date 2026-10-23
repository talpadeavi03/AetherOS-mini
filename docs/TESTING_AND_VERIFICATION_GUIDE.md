# AetherOS Subsystem Testing & Operational Verification Guide

Welcome to the **AetherOS Complete Testing & Verification Guide**. This document provides hands-on, step-by-step instructions to test and verify every component and neuro-daemon across the entire operating system stack.

---

## 📑 Table of Contents

1. [Quick Start: One-Click Automated Test Suite](#1-quick-start-one-click-automated-test-suite)
2. [Component 1: Kernel MCP NeuroBus (`aether-mcpd`)](#component-1-kernel-mcp-neurobus-aether-mcpd)
3. [Component 2: Vision Sensory Engine (`aether-visiond`)](#component-2-vision-sensory-engine-aether-visiond)
4. [Component 3: Voice Intelligence & Speech Core (`aether-voiced`)](#component-3-voice-intelligence--speech-core-aether-voiced)
5. [Component 4: Vector Memory Vault & Knowledge Graph (`aether-memd`)](#component-4-vector-memory-vault--knowledge-graph-aether-memd)
6. [Component 5: Micro-Intent Router (`aether-intentd`)](#component-5-micro-intent-router-aether-intentd)
7. [Component 6: Autonomous Agent Swarm (`aether-agentd`)](#component-6-autonomous-agent-swarm-aether-agentd)
8. [Component 7: Spatial Neural HUD (`aether-hud`)](#component-7-spatial-neural-hud-aether-hud)
9. [Component 8: OS-Native MLOps & SIMD Compute Engine (`aether-mlopsd`)](#component-8-os-native-mlops--simd-compute-engine-aether-mlopsd)
10. [Component 9: Terminal AI Developer Copilot (`aether-assist`)](#component-9-terminal-ai-developer-copilot-aether-assist)
11. [Component 10: Robotics & ROS 2 Sensor Fusion Hub (`aether-roboticsd`)](#component-10-robotics--ros-2-sensor-fusion-hub-aether-roboticsd)
12. [Component 11: Compositor & Hyprdots UI Controls](#component-11-compositor--hyprdots-ui-controls)
13. [Troubleshooting & Diagnostics Checklist](#troubleshooting--diagnostics-checklist)

---

## 1. Quick Start: One-Click Automated Test Suite

AetherOS includes automated test runners that query all 8 neuro-daemons over local Unix domain sockets or the local network bridge.

### Running from Inside the Operating System (Terminal)
Inside any terminal in AetherOS (Foot or Kitty), run:
```bash
aetherctl test
```
*Or execute the test binary directly:*
```bash
/usr/bin/aether-test
```

### Running from the Host Machine (Over Network Bridge)
If testing a virtual machine instance running under QEMU / KVM / Virtual Machine Manager:
```bash
python3 scripts/test_vm_network_and_local.py
```
*(The script automatically queries `virsh domifaddr AetherOS-Mini` to resolve the dynamic VM IP and benchmarks all 8 endpoints).*

**Expected Output:**
```
══════════════════════════════════════════════════════════════════════════════════
                         OVERALL VERIFICATION MATRIX                             
══════════════════════════════════════════════════════════════════════════════════
  ✔ PASS Kernel MCP NeuroBus (:9090)          (4 tools, 14.55ms)
  ✔ PASS Vision Sensory Engine (:9091)        (User: aether (98%), 3.29ms)
  ✔ PASS Voice Intelligence (:9092)           (Synth: SYNTHESIZING, 5.12ms)
  ✔ PASS Vector Memory Vault (:9093)          (Cosine sim: 0.679, 4.05ms)
  ✔ PASS Micro-Intent Router (:9094)          ('system.diagnose' in 25.72ms)
  ✔ PASS Autonomous Agent Swarm (:9095)       (4/4 agents nominal, heal 39.15ms)
  ✔ PASS Native MLOps Engine (:9096)          (43.4 MFLOPS on HIGH_THROUGHPUT_AVX2)
  ✔ PASS Robotics Sensor Fusion (:9097)       (Mode: AUTONOMOUS_READY, Nav: ENGAGED)
══════════════════════════════════════════════════════════════════════════════════
  ALL 8 NEURO-DAEMONS & ROBOTICS HUB PASSED WITH 100% SUCCESS!
```

---

## Component 1: Kernel MCP NeuroBus (`aether-mcpd`)

Exposes real-time kernel telemetry, PSI (Pressure Stall Information), memory pressure, and cgroup tracking over Model Context Protocol (MCP).

- **Unix Socket:** `/run/aether/mcp.sock`
- **HTTP Endpoint:** Port `9090`
- **Systemd Unit:** `aether-mcp.service`

### How to Test

#### 1. CLI Diagnostic:
```bash
aetherctl status
```
#### 2. Trigger Memory Compaction via MCP:
```bash
aetherctl compact
```
#### 3. Inspect Running Threads:
```bash
aetherctl threads
```
#### 4. Direct HTTP API Verification (from Host or Terminal):
```bash
# List exposed MCP tools
curl -s http://localhost:9090/tools | jq .

# Call system.diagnose tool
curl -s -X POST http://localhost:9090/tool/system.diagnose | jq .
```

**Expected JSON Response:**
```json
{
  "tool": "system.diagnose",
  "result": {
    "status": "OPTIMAL",
    "ram_used_mb": 821,
    "ram_total_mb": 1958,
    "ram_available_mb": 1137,
    "active_threads": 250,
    "psi": {
      "cpu": "some avg10=0.00 avg60=0.00 avg300=0.03 total=7598296",
      "memory": "some avg10=0.00 avg60=0.00 avg300=0.00 total=4",
      "io": "some avg10=0.00 avg60=0.00 avg300=0.03 total=10144598"
    },
    "issues": [],
    "recommendation": "All subsystems nominal."
  }
}
```

---

## Component 2: Vision Sensory Engine (`aether-visiond`)

Provides continuous biometric authentication, gaze focus vector tracking, Eye Aspect Ratio (EAR) blink rate, head pose estimation, and ergonomic posture classification.

- **Unix Socket:** `/run/aether/vision.sock`
- **HTTP Endpoint:** Port `9091`
- **Systemd Unit:** `aether-vision.service`

### How to Test

#### 1. CLI Telemetry Inspection:
```bash
aetherctl vision
```

#### 2. HTTP Endpoint Verification:
```bash
curl -s http://localhost:9091/status | jq .
```

**Expected Output:**
```json
{
  "biometrics": {
    "authenticated_user": "aether",
    "confidence": 0.98,
    "face_detected": true
  },
  "gaze": {
    "focus_region": "center_terminal",
    "vector": [-0.094, 0.034]
  },
  "ergonomics": {
    "blink_rate_bpm": 18.0,
    "ear": 0.32,
    "fatigue_index": 0.08,
    "posture": "upright_ergonomic",
    "head_pose": { "pitch": 0.6, "yaw": -0.8, "roll": 0.2 }
  }
}
```

---

## Component 3: Voice Intelligence & Speech Core (`aether-voiced`)

Manages phonetic and neural text-to-speech synthesis (`espeak-ng`), voice activity detection (VAD), and meeting/interactive listening modes.

- **Unix Socket:** `/run/aether/voice.sock`
- **HTTP Endpoint:** Port `9092`
- **Systemd Unit:** `aether-voice.service`

### How to Test

#### 1. Test Speech Synthesis via CLI:
```bash
aetherctl voice speak "AetherOS sensory core is verified and fully functional."
```

#### 2. Change Voice Listening Mode:
```bash
# Switch to meeting mode
aetherctl voice mode meeting_mode

# Switch back to interactive mode
aetherctl voice mode interactive
```

#### 3. Test HTTP Speech API:
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"text": "Subsystem test passed successfully."}' \
  http://localhost:9092/speak | jq .
```

---

## Component 4: Vector Memory Vault & Knowledge Graph (`aether-memd`)

Manages the persistent SQLite episodic vector vault with cosine similarity search and the user/system Knowledge Graph.

- **Database Path:** `/var/lib/aether/memory.db`
- **Unix Socket:** `/run/aether/mem.sock`
- **HTTP Endpoint:** Port `9093`
- **Systemd Unit:** `aether-memory.service`

### How to Test

#### 1. Store an Episodic Memory Note:
```bash
aetherctl memory store "robotics" "Tested ROS 2 waypoint navigation in sector 4"
```

#### 2. Perform a Semantic Vector Search:
```bash
aetherctl memory search "waypoint navigation"
```
*(Uses 128-dimensional cosine vector embeddings to match semantically relevant notes).*

#### 3. Inspect Knowledge Graph Edges:
```bash
aetherctl memory graph
```

#### 4. Test HTTP Search API:
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"query": "robotics waypoint", "limit": 3}' \
  http://localhost:9093/search | jq .
```

---

## Component 5: Micro-Intent Router (`aether-intentd`)

Routes natural language text or speech into deterministic system commands, MCP tool calls, or cognitive reasoning tiers in **$< 25\text{ ms}$**.

- **Unix Socket:** `/run/aether/intent.sock`
- **HTTP Endpoint:** Port `9094`
- **Systemd Unit:** `aether-intent.service`

### How to Test

#### 1. Dispatch Direct System Intent:
```bash
aetherctl intent "diagnose my system"
```

#### 2. Dispatch DevOps Intent:
```bash
aetherctl intent "prepare devops environment"
```

#### 3. Dispatch Memory Intent:
```bash
aetherctl intent "search memory for robotics"
```

#### 4. Conversational Chat Mode with Audio Feedback:
```bash
aetherctl chat "What is my current ergonomic posture?"
```

#### 5. Benchmark Latency via HTTP:
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"prompt": "diagnose system"}' \
  http://localhost:9094/route | jq '{intent, tier, latency_ms}'
```
*Verify that `latency_ms` is under 25ms.*

---

## Component 6: Autonomous Agent Swarm (`aether-agentd`)

Coordinates 4 resident agents:
1. **SentinelAgent**: Continuous PSI monitor & self-healing recovery.
2. **SecurityAgent**: Continuous Zero-Trust biometric identity verification.
3. **DevOpsAgent**: Repository observation and environment provisioning.
4. **HealthAgent**: Ergonomics, blink rate, and 20-20-20 rule strain guardian.

- **Unix Socket:** `/run/aether/agent.sock`
- **HTTP Endpoint:** Port `9095`
- **Systemd Unit:** `aether-agent.service`

### How to Test

#### 1. Inspect All 4 Agents:
```bash
aetherctl agent status
```

#### 2. Trigger Autonomous Self-Healing:
```bash
aetherctl agent heal
```
*Sentinel will compact vector storage, flush filesystem dirty pages, and verify daemon heartbeats.*

#### 3. Trigger DevOps Environment Provisioning:
```bash
aetherctl agent devops
```

#### 4. Test Over HTTP API:
```bash
# Get overall swarm status
curl -s http://localhost:9095/status | jq .agents

# Dispatch action to Sentinel
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"agent": "sentinel", "action": "heal", "params": {"reason": "Manual operator test"}}' \
  http://localhost:9095/action | jq .
```

---

## Component 7: Spatial Neural HUD (`aether-hud`)

Holographic floating HUD in Hyprland with Catppuccin Mocha glassmorphism, animated Quantum Iris, audio visualizer, 4-agent matrix, and micro-intent prompt.

- **Binary:** `/usr/bin/aether-hud`
- **Compositor Hotkey:** **`Super` + `Space`** or **`Super` + `A`**
- **Window Rules:** Floating `960x640`, centered, gradient border.

### How to Test

1. Press **`Super` + `Space`** (or run `aetherctl hud` in terminal).
2. The HUD floats centered on the screen with:
   - Animated Quantum Core Iris (pulsating energy circle in Cyan/Violet).
   - Audio visualizer waves (` ▂▃▅▆▇█`).
   - 4-Agent status cards (Sentinel, Security, DevOps, Health).
   - Real-time Kernel NeuroBus latency monitor.
3. Type any natural language prompt directly into the prompt:
   - Type `prepare devops` and press **Enter** (dispatches in $15\text{ms}$).
   - Type `diagnose system` and press **Enter** (diagnoses system in $21\text{ms}$).
   - Type `heal` and press **Enter** (triggers Sentinel self-healing).
4. Press **`q`** or **Ctrl+C** to exit standby.

---

## Component 8: OS-Native MLOps & SIMD Compute Engine (`aether-mlopsd`)

Manifest-driven Model Registry managing local SLMs, ONNX weights, GGUF quantized models, and hardware acceleration profiler (AVX2, FMA, Vulkan).

- **Registry Directory:** `/var/lib/aether/models/`
- **Unix Socket:** `/run/aether/mlops.sock`
- **HTTP Endpoint:** Port `9096`
- **Systemd Unit:** `aether-mlops.service`

### How to Test

#### 1. Inspect Hardware Acceleration & Model Registry:
```bash
aetherctl mlops status
```

#### 2. List All Registered Models:
```bash
aetherctl mlops models
```

#### 3. Run Live SIMD Float Benchmark:
```bash
aetherctl mlops benchmark
```
*(Measures local CPU vector float multiplication throughput in MFLOPS).*

#### 4. Switch Active Tier Model:
```bash
aetherctl mlops switch reasoning aether-reasoning-slm-3b
```

#### 5. Direct HTTP Benchmark:
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"iterations": 150000}' \
  http://localhost:9096/benchmark | jq .
```

---

## Component 9: Terminal AI Developer Copilot (`aether-assist`)

Translates natural language developer intents into valid shell commands, explains command errors, and synthesizes Git commits.

- **Binaries:** `/usr/bin/aether-assist`, `/usr/bin/aether-fix`, `/usr/bin/aether-git-commit`

### How to Test

#### 1. Natural Language Command Synthesis:
```bash
aetherctl assist "find large files"
```
*Expected: Suggests `find / -type f -size +100M -exec ls -lh {} + 2>/dev/null` with flag explanations.*

```bash
aetherctl assist "show listening ports"
```
*Expected: Suggests `ss -tulwn`.*

#### 2. Analyze & Fix Last Failed Shell Command:
Run an intentional error in Bash, then run:
```bash
aetherctl fix
```
*Analyzes the last history entry, detects root cause (e.g. missing permissions, wrong package manager), and prints the resolution.*

#### 3. Automated Git Commit Authoring:
Stage some changes with `git add`, then run:
```bash
aetherctl git
```
*Analyzes `git diff --cached` and synthesizes a conventional commit message (e.g. `feat(core): update ...`).*

---

## Component 10: Robotics & ROS 2 Sensor Fusion Hub (`aether-roboticsd`)

Bridges the operating system to the physical world, offering real-time 6-DoF IMU attitude tracking, 360-degree LiDAR perimeter mapping, and autonomous waypoint navigation over MCP.

- **Unix Socket:** `/run/aether/robotics.sock`
- **HTTP Endpoint:** Port `9097`
- **Systemd Unit:** `aether-robotics.service`

### How to Test

#### 1. Inspect Robotics Status:
```bash
aetherctl robot status
```
*Displays robot mode (`AUTONOMOUS_READY`), battery percentage, spatial pose $(x, y, \theta)$, and IMU calibration status.*

#### 2. Inspect 360-Degree LiDAR Range Sectors:
```bash
aetherctl robot lidar
```
*Returns distances in meters across 8 sectors (`front`, `front_right`, `right`, `back_right`, `back`, `back_left`, `left`, `front_left`).*

#### 3. Inspect 6-DoF IMU Attitude:
```bash
aetherctl robot imu
```
*Returns roll, pitch, yaw, accelerations $(a_x, a_y, a_z)$, and angular rates.*

#### 4. Dispatch Autonomous Waypoint Navigation:
```bash
aetherctl robot navigate 2.5 1.2
```
*Engages autonomous pathfinding to coordinates $(x=2.5\text{m}, y=1.2\text{m})$. Emits a glowing notification pill into Hyprland when waypoint is reached.*

#### 5. Direct HTTP Navigation Test:
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"x": 3.0, "y": 1.5, "theta": 90.0}' \
  http://localhost:9097/navigate | jq .
```

---

## Component 11: Compositor & Hyprdots UI Controls

AetherOS runs on Hyprland 0.56 with a customized Catppuccin Mocha glassmorphic theme.

### Keybinding Quick Reference

| Keybinding | Action |
| :--- | :--- |
| **`Super` + `Space`** / **`Super` + `A`** | Toggle **Spatial Neural HUD** (`aether-hud`) |
| **`Super` + `Enter`** / **`Super` + `T`** | Open Foot Terminal |
| **`Super` + `S`** | Real-Time Sensory Vision Telemetry (`aetherctl vision`) |
| **`Super` + `C`** | Trigger Sentinel Self-Healing & Memory Compaction |
| **`Super` + `M`** | Inspect Episodic Knowledge Graph |
| **`Super` + `D`** | Hyprdots Rofi Application Launcher |
| **`Super` + `Q`** | Close Active Window (`killactive`) |
| **`Super` + `V`** / **`Super` + `W`** | Toggle Window Floating Mode |
| **`Super` + `F`** | Toggle Fullscreen Mode |
| **`Super` + `1` – `9`** | Switch Workspaces |
| **`Super` + `Shift` + `1` – `9`** | Move Active Window to Workspace |

### Waybar Interactive Status Pills (Top Panel)
- **`󰈈 Vision Active`** (Cyan): Clicking launches sensory vision telemetry window.
- **`󰚩 Neural HUD`** (Violet): Clicking opens the Spatial Neural HUD.
- **`󰍛 0.8GB`** (Memory): Clicking triggers kernel memory compaction.

---

## Troubleshooting & Diagnostics Checklist

### 1. Check Systemd Units
Ensure all 8 core services are active:
```bash
systemctl status aether-mcp.service \
                 aether-vision.service \
                 aether-voice.service \
                 aether-memory.service \
                 aether-intent.service \
                 aether-agent.service \
                 aether-mlops.service \
                 aether-robotics.service
```

### 2. Verify Unix Sockets
Check that all `/run/aether/*.sock` files exist:
```bash
ls -la /run/aether/
```
*Expected: `mcp.sock`, `vision.sock`, `voice.sock`, `mem.sock`, `intent.sock`, `agent.sock`, `mlops.sock`, `robotics.sock`.*

### 3. Restart Any Service
If any daemon was stopped:
```bash
sudo systemctl restart aether-agent.service
# or restart all
sudo systemctl restart aether-*.service
```

---

*Authored by the AetherOS Systems & AI Engineering Team.*  
*Repository: [https://github.com/talpadeavi03/AetherOS-mini](https://github.com/talpadeavi03/AetherOS-mini)*  
*Branch: `2.0`*
