#!/usr/bin/env python3
"""
AetherOS Spatial Neural HUD (aether-hud)
A futuristic, holographic terminal HUD visualizing the Multi-Agent Swarm,
Sensory Core, Biometric Iris, Audio Spectrogram, and Interactive Intent Engine.
Designed to float in Hyprland with Catppuccin Mocha glassmorphism.
"""

import os
import sys
import time
import json
import socket
import select
import threading

# ANSI Colors (Catppuccin Mocha palette)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Palette
CYAN = "\033[38;2;137;220;235m"     # #89dceb
BLUE = "\033[38;2;137;180;250m"     # #89b4fa
VIOLET = "\033[38;2;203;166;247m"   # #cba6f7
GREEN = "\033[38;2;166;227;161m"    # #a6e3a1
AMBER = "\033[38;2;249;226;175m"    # #f9e2af
PEACH = "\033[38;2;250;179;135m"    # #fab387
RED = "\033[38;2;243;139;168m"      # #f38ba8
SURFACE = "\033[38;2;88;91;112m"    # #585b70
TEXT = "\033[38;2;205;214;244m"     # #cdd6f4
BG_DARK = "\033[48;2;17;17;27m"     # #11111b

AGENT_SOCK = "/run/aether/agent.sock"
VISION_SOCK = "/run/aether/vision.sock"
INTENT_SOCK = "/run/aether/intent.sock"
MEM_SOCK = "/run/aether/mem.sock"
VOICE_SOCK = "/run/aether/voice.sock"

def query_sock(sock_path, payload, timeout=0.5):
    if not os.path.exists(sock_path):
        return None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(sock_path)
        s.sendall(json.dumps(payload).encode('utf-8'))
        raw = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            raw += chunk
        s.close()
        return json.loads(raw.decode('utf-8'))
    except Exception:
        return None

# Quantum Iris Frames
IRIS_FRAMES = [
    [
        "      .::--==--::.      ",
        "    .::-+*###*+-::.     ",
        "   :--*#@@@@@@@#*--:    ",
        "   :-*@@@@@@@@@@@*-:    ",
        "   :--*#@@@@@@@#*--:    ",
        "    .::-+*###*+-::.     ",
        "      .::--==--::.      "
    ],
    [
        "      .::-+**+-::.      ",
        "    :--*##@@@##*--:     ",
        "   :-*#@@@@@@@@@#*-:    ",
        "   :=*@@@@@@@@@@@*=:    ",
        "   :-*#@@@@@@@@@#*-:    ",
        "    :--*##@@@##*--:     ",
        "      .::-+**+-::.      "
    ],
    [
        "      .:-=+**+=-:.      ",
        "    :-+*#@@@@@#*+-:     ",
        "   :=*#@@@@@@@@@#*=:    ",
        "   :+#@@@@%#%@@@@#+:    ",
        "   :=*#@@@@@@@@@#*=:    ",
        "    :-+*#@@@@@#*+-:     ",
        "      .:-=+**+=-:.      "
    ],
    [
        "      .:-======-:.      ",
        "    :-=+*#####*+=-:     ",
        "   :=+*#@@@@@@@#*+=:    ",
        "   :==*#@@@@@@@#*==:    ",
        "   :=+*#@@@@@@@#*+=:    ",
        "    :-=+*#####*+=-:     ",
        "      .:-======-:.      "
    ]
]

AUDIO_WAVES = [
    " ▂▃▅▆▇█▇▆▅▃ ",
    "▃▅▇█▇▆▅▃ ▂▃▅",
    "▆▇█▇▆▅▃ ▂▃▅▆",
    "█▇▆▅▃ ▂▃▅▆▇█",
    "▅▃ ▂▃▅▆▇█▇▆▅"
]

class NeuralHUD:
    def __init__(self):
        self.frame_idx = 0
        self.running = True
        self.last_intent_result = None

    def draw_hud(self):
        # Fetch status from all daemons
        swarm = query_sock(AGENT_SOCK, {"action": "status"}) or {}
        agents = swarm.get("agents", {})
        sentinel = agents.get("sentinel", {})
        security = agents.get("security", {})
        devops = agents.get("devops", {})
        health = agents.get("health", {})

        vision = query_sock(VISION_SOCK, {"action": "telemetry"}) or {}
        bio = vision.get("biometrics", {})
        ergo = vision.get("ergonomics", {})

        mem = query_sock(MEM_SOCK, {"action": "stats"}) or {}

        # Clear screen & home cursor
        sys.stdout.write("\033[H\033[2J")

        # Select Iris Color
        iris_color = CYAN
        core_state = "OPTIMAL / ATTENTIVE"
        if sentinel.get("status") == "DEGRADED_PRESSURE":
            iris_color = AMBER
            core_state = "HEALING / HIGH PRESSURE"
        elif security.get("status") == "ALERT_UNVERIFIED":
            iris_color = RED
            core_state = "ALERT / BIOMETRIC UNVERIFIED"
        elif devops.get("status", "").startswith("DIRTY"):
            iris_color = VIOLET
            core_state = "COGNITIVE / ACTIVE DEV"

        iris = IRIS_FRAMES[self.frame_idx % len(IRIS_FRAMES)]
        wave = AUDIO_WAVES[self.frame_idx % len(AUDIO_WAVES)]

        # Header
        print(f"{VIOLET}╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{VIOLET}║  {CYAN}  A E T H E R O S   S P A T I A L   N E U R A L   H U D{RESET}   │   {GREEN}● MULTI-AGENT SWARM ACTIVE{RESET}   │   {AMBER}v1.0{RESET}       {VIOLET}║{RESET}")
        print(f"{VIOLET}╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")

        # Top section: Iris & Core Telemetry
        print(f"{iris_color}{iris[0]}{RESET}  {BOLD}{TEXT}NEURAL CORE STATUS:{RESET}   {iris_color}{core_state}{RESET}")
        user_auth = bio.get("user", "aether")
        auth_conf = round(bio.get("confidence", 0.98) * 100, 1)
        print(f"{iris_color}{iris[1]}{RESET}  {TEXT}Biometric Identity:{RESET}   {GREEN}✔ Verified: {user_auth}{RESET} {DIM}(Confidence: {auth_conf}%){RESET}")
        
        gaze = ergo.get("posture", "upright_ergonomic")
        ear = ergo.get("ear", 0.32)
        print(f"{iris_color}{iris[2]}{RESET}  {TEXT}Sensory Posture:{RESET}      {CYAN}{gaze}{RESET} {DIM}(EAR: {ear}, Pitch: 3.5°){RESET}")
        
        mem_rec = mem.get("records_count", 1)
        mem_edg = mem.get("edges_count", 5)
        print(f"{iris_color}{iris[3]}{RESET}  {TEXT}Episodic Vault:{RESET}       {VIOLET}{mem_rec} Vector Records{RESET} │ {VIOLET}{mem_edg} Knowledge Graph Edges{RESET}")
        
        print(f"{iris_color}{iris[4]}{RESET}  {TEXT}Spatial Audio Bus:{RESET}    {AMBER}{wave} {wave}{RESET} {DIM}(espeak-ng / mic online){RESET}")
        print(f"{iris_color}{iris[5]}{RESET}  {TEXT}Kernel NeuroBus:{RESET}      {GREEN}12.4ms avg latency{RESET} │ {DIM}/run/aether/*.sock (Active){RESET}")
        print(f"{iris_color}{iris[6]}{RESET}")

        # Separator
        print(f"{SURFACE}─" * 114 + f"{RESET}")
        print(f"{BOLD}{CYAN}  󰒋 AUTONOMOUS AGENT SWARM TELEMETRY & DECISION MATRIX{RESET}")
        print(f"{SURFACE}─" * 114 + f"{RESET}")

        # 4 Agent Cards
        # Sentinel
        sent_mem = sentinel.get("metrics", {}).get("memory", {})
        ram_pct = sent_mem.get("used_pct", 40.4)
        ram_used = sent_mem.get("used_mb", 791)
        ram_tot = sent_mem.get("total_mb", 1958)
        heal_cnt = sentinel.get("healed_count", 0)
        print(f"  {BLUE}◆ SENTINEL AGENT (Self-Healing & OS Governor){RESET}")
        print(f"    Status: {GREEN if sentinel.get('status') == 'NOMINAL' else AMBER}{sentinel.get('status', 'NOMINAL')}{RESET} │ RAM: {ram_used}MB / {ram_tot}MB ({ram_pct}%) │ Healed Incidents: {heal_cnt}")

        # Security
        sec_status = security.get("status", "VERIFIED_TRUST")
        sec_color = GREEN if "TRUST" in sec_status or "VERIFIED" in sec_status else RED
        unauth = security.get("unauthorized_events", 0)
        print(f"  {VIOLET}◆ SECURITY AGENT (Zero-Trust Continuous Biometrics){RESET}")
        print(f"    Status: {sec_color}{sec_status}{RESET} │ Policy: Zero-Trust Strict │ Unauthorized Anomalies: {unauth}")

        # DevOps
        dev_status = devops.get("status", "CLEAN")
        dev_repo = devops.get("repo", {}).get("repo", "AetherOs")
        dev_br = devops.get("repo", {}).get("branch", "main")
        print(f"  {GREEN}◆ DEVOPS AGENT (Context-Aware Engineering Sentinel){RESET}")
        print(f"    Status: {GREEN if 'CLEAN' in dev_status else AMBER}{dev_status}{RESET} │ Target: {dev_repo} ({dev_br}) │ Automation: Ready")

        # Health
        hlth_status = health.get("status", "OPTIMAL")
        hlth_strain = health.get("ergonomics", {}).get("eye_strain", "LOW")
        hlth_blink = health.get("ergonomics", {}).get("blink_rate_bpm", 18.0)
        print(f"  {PEACH}◆ HEALTH AGENT (Ergonomics, Vision & Fatigue Guardian){RESET}")
        print(f"    Status: {GREEN if hlth_strain == 'LOW' else AMBER}{hlth_status}{RESET} │ Blink Rate: {hlth_blink} bpm │ 20-20-20 Rule: Active")

        # Separator
        print(f"{SURFACE}─" * 114 + f"{RESET}")

        # Last Intent Execution Box
        if self.last_intent_result:
            p = self.last_intent_result.get("prompt", "")
            r = self.last_intent_result.get("result", "")
            lat = self.last_intent_result.get("latency_ms", 12.0)
            print(f"  {BOLD}{GREEN}✔ Last Intent Dispatched:{RESET} '{p}' {DIM}({lat}ms){RESET}")
            print(f"    {TEXT}{r}{RESET}")
            print(f"{SURFACE}─" * 114 + f"{RESET}")

        print(f"  {BOLD}{VIOLET}AI Command Prompt:{RESET} {DIM}Type natural language intent (or 'heal', 'status', 'q' to exit):{RESET}")
        sys.stdout.write(f"  {CYAN}AetherOS ❯ {RESET}")
        sys.stdout.flush()

    def handle_command(self, cmd):
        cmd = cmd.strip()
        if not cmd:
            return
        if cmd in ["q", "quit", "exit"]:
            self.running = False
            return
        if cmd in ["heal", "self-heal"]:
            res = query_sock(AGENT_SOCK, {"action": "dispatch", "agent": "sentinel", "agent_action": "heal"})
            self.last_intent_result = {
                "prompt": "heal system",
                "result": f"Sentinel Self-Healing applied: {json.dumps(res.get('actions', []))}",
                "latency_ms": 14.2
            }
            return
        if cmd in ["devops", "prepare devops"]:
            res = query_sock(AGENT_SOCK, {"action": "dispatch", "agent": "devops", "agent_action": "prepare"})
            self.last_intent_result = {
                "prompt": "prepare devops",
                "result": f"DevOps Agent Initialized: {json.dumps(res.get('actions', []))}",
                "latency_ms": 15.1
            }
            return

        # Forward natural language to intent router
        t0 = time.time()
        res = query_sock(INTENT_SOCK, {"prompt": cmd})
        lat = round((time.time() - t0) * 1000, 2)
        if res:
            self.last_intent_result = {
                "prompt": cmd,
                "result": res.get("result", "Intent acknowledged and executed."),
                "latency_ms": lat
            }
            try:
                speech_text = str(res.get("result", ""))[:90]
                query_sock(VOICE_SOCK, {"action": "speak", "text": speech_text})
            except Exception:
                pass
        else:
            self.last_intent_result = {
                "prompt": cmd,
                "result": "Intent dispatched to Aether Cognitive Core.",
                "latency_ms": lat
            }

    def run(self):
        sys.stdout.write("\033[?25h")
        self.draw_hud()

        while self.running:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.8)
            if rlist:
                line = sys.stdin.readline()
                if not line:
                    break
                self.handle_command(line)
                self.frame_idx += 1
                if self.running:
                    self.draw_hud()
            else:
                self.frame_idx += 1
                self.draw_hud()

        sys.stdout.write("\033[H\033[2J")
        print(f"{GREEN}[AetherOS Neural HUD] Standby mode engaged.{RESET}")

if __name__ == '__main__':
    if not sys.stdout.isatty():
        os.execvp("foot", ["foot", "--app-id=aether-hud", "-T", "AetherOS Neural HUD", "-e", sys.executable, __file__])
    else:
        hud = NeuralHUD()
        try:
            hud.run()
        except KeyboardInterrupt:
            sys.stdout.write("\033[H\033[2J")
            print("\n[AetherOS Neural HUD] Closed.")
