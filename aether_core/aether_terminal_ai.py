#!/usr/bin/env python3
"""
AetherOS Terminal AI Copilot (`aether-assist` / `aether-fix`)
Developer Experience utility providing natural language CLI synthesis,
intelligent failure recovery, and automated Git commit authoring.
"""

import os
import sys
import json
import socket
import subprocess

INTENT_SOCK = "/run/aether/intent.sock"
MEM_SOCK = "/run/aether/mem.sock"
MCP_SOCK = "/run/aether/mcp.sock"

# ANSI Colors
CYAN = "\033[38;2;137;220;235m"
GREEN = "\033[38;2;166;227;161m"
AMBER = "\033[38;2;249;226;175m"
VIOLET = "\033[38;2;203;166;247m"
RED = "\033[38;2;243;139;168m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

COMMON_SYNTHESIS_PATTERNS = [
    ("find large files", "find / -type f -size +100M -exec ls -lh {} + 2>/dev/null", "Find all files larger than 100MB"),
    ("open ports", "ss -tulwn", "Show all listening TCP and UDP sockets with numeric addresses"),
    ("kill port", "fuser -k -n tcp <port>", "Kill the process holding the given TCP port"),
    ("disk usage", "df -h -x tmpfs -x devtmpfs", "Display clean disk usage for physical partitions"),
    ("memory usage", "free -h", "Show available and cached physical memory"),
    ("git undo last commit", "git reset --soft HEAD~1", "Undo the last commit while keeping changes staged"),
    ("git discard all changes", "git restore . && git clean -fd", "Discard all modified and untracked files"),
    ("container list", "docker ps -a || podman ps -a", "List all active and stopped containers"),
    ("service logs", "journalctl -u <service> -e -f", "Follow live systemd service logs from end")
]

def query_sock(sock_path, payload, timeout=1.5):
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

def assist_query(query):
    query_lower = query.lower()
    matched_cmd = None
    matched_desc = None

    for pattern, cmd, desc in COMMON_SYNTHESIS_PATTERNS:
        if pattern in query_lower:
            matched_cmd = cmd
            matched_desc = desc
            break

    print(f"\n{BOLD}{CYAN}  AetherOS Terminal AI Copilot{RESET}")
    print(f"{DIM}──────────────────────────────────────────────────{RESET}")
    print(f"{BOLD}Query:{RESET} '{query}'")

    if matched_cmd:
        print(f"\n{BOLD}{GREEN}Suggested Command:{RESET}")
        print(f"  {VIOLET}❯ {matched_cmd}{RESET}")
        print(f"\n{DIM}Purpose: {matched_desc}{RESET}")
        print(f"{DIM}Press Enter to execute or Ctrl+C to cancel.{RESET}")
    else:
        # Route to Intent Engine
        res = query_sock(INTENT_SOCK, {"prompt": query})
        if res:
            print(f"\n{BOLD}{GREEN}Aether Cognitive Response:{RESET}")
            print(f"  {res.get('result')}")
            print(f"\n{DIM}(Intent: {res.get('intent')}, Latency: {res.get('latency_ms')}ms){RESET}")
        else:
            print(f"\n{AMBER}No direct command pattern match. Consulted local SLM.{RESET}")

    print(f"{DIM}──────────────────────────────────────────────────{RESET}\n")

def fix_last_command():
    # Read last line from bash history
    hist_file = os.path.expanduser("~/.bash_history")
    last_cmd = "unknown"
    if os.path.exists(hist_file):
        try:
            with open(hist_file, "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                if lines:
                    last_cmd = lines[-1]
        except Exception:
            pass

    print(f"\n{BOLD}{RED}󰅚  AetherOS Failure Analysis & Auto-Fix{RESET}")
    print(f"{DIM}──────────────────────────────────────────────────{RESET}")
    print(f"{BOLD}Failed Command:{RESET} {VIOLET}{last_cmd}{RESET}")

    # Heuristic Fix Engine
    fixed_cmd = None
    reason = None

    if "permission denied" in last_cmd.lower() or not last_cmd.startswith("sudo"):
        fixed_cmd = f"sudo {last_cmd}"
        reason = "Command requires elevated root / hardware permissions"
    elif "apt" in last_cmd:
        fixed_cmd = last_cmd.replace("apt", "pacman -S")
        reason = "AetherOS uses pacman package manager on Arch Linux base"
    elif "systemctl" in last_cmd and not last_cmd.startswith("sudo"):
        fixed_cmd = f"sudo {last_cmd}"
        reason = "Systemd service control requires administrative privileges"

    if fixed_cmd:
        print(f"{BOLD}Analysis:{RESET} {reason}")
        print(f"\n{BOLD}{GREEN}Recommended Resolution:{RESET}")
        print(f"  {CYAN}❯ {fixed_cmd}{RESET}")
    else:
        print(f"{BOLD}Analysis:{RESET} Syntax or runtime error detected.")
        print(f"{BOLD}Recommendation:{RESET} Verify arguments with '{last_cmd.split()[0]} --help' or query 'aether-assist'.")

    print(f"{DIM}──────────────────────────────────────────────────{RESET}\n")

def auto_git_commit():
    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        if not status:
            print(f"{AMBER}[Aether Git] No staged or modified changes to commit.{RESET}")
            return
        
        diff = subprocess.check_output(["git", "diff", "--cached", "--stat"], text=True).strip()
        lines = status.splitlines()
        modified = [l[3:] for l in lines]
        
        # Determine conventional category
        category = "feat"
        if any("test" in f for f in modified):
            category = "test"
        elif any("doc" in f or "README" in f for f in modified):
            category = "docs"
        elif any("fix" in f for f in modified):
            category = "fix"

        summary = f"{category}(core): update {', '.join([os.path.basename(f) for f in modified[:3]])}"
        print(f"\n{BOLD}{CYAN}  AetherOS Automated Git Commit Synthesizer{RESET}")
        print(f"{DIM}──────────────────────────────────────────────────{RESET}")
        print(f"{BOLD}Synthesized Message:{RESET} {GREEN}{summary}{RESET}")
        print(f"{BOLD}Changed Files ({len(lines)}):{RESET}")
        for l in lines[:5]:
            print(f"  {DIM}{l}{RESET}")
        print(f"{DIM}──────────────────────────────────────────────────{RESET}")
        print(f"{CYAN}Run: git commit -m \"{summary}\"{RESET}\n")
    except Exception as e:
        print(f"{RED}Error analyzing git workspace: {e}{RESET}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  aether-assist \"<query>\"    Synthesize shell commands from natural language")
        print("  aether-fix                  Analyze last failed command and generate resolution")
        print("  aether-git-commit           Synthesize conventional git commit from changes")
        return

    cmd = sys.argv[1]
    if cmd in ["fix", "--fix"]:
        fix_last_command()
    elif cmd in ["git", "git-commit", "--git"]:
        auto_git_commit()
    else:
        query = " ".join(sys.argv[1:])
        assist_query(query)

if __name__ == '__main__':
    main()
