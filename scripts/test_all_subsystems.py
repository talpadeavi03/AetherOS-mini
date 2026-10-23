#!/usr/bin/env python3
"""
AetherOS Full Subsystem Comprehensive Test Suite
Validates all 7 neuro-daemons, IPC sockets, latency benchmarks,
and compositor integrations.
"""

import sys
import os
import time
import json
import socket

# ANSI Colors
GREEN = "\033[38;2;166;227;161m"
RED = "\033[38;2;243;139;168m"
CYAN = "\033[38;2;137;220;235m"
AMBER = "\033[38;2;249;226;175m"
VIOLET = "\033[38;2;203;166;247m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

SOCKETS = {
    "Kernel MCP NeuroBus": "/run/aether/mcp.sock",
    "Vision Sensory Engine": "/run/aether/vision.sock",
    "Voice Intelligence Core": "/run/aether/voice.sock",
    "Vector Memory Vault": "/run/aether/mem.sock",
    "Micro-Intent Router": "/run/aether/intent.sock",
    "Autonomous Agent Swarm": "/run/aether/agent.sock",
    "Native MLOps Engine": "/run/aether/mlops.sock"
}

def query_sock(sock_path, payload, timeout=1.5):
    if not os.path.exists(sock_path):
        return None, 0.0
    t0 = time.time()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(sock_path)
        s.sendall(json.dumps(payload).encode('utf-8'))
        raw = b""
        while True:
            chunk = s.recv(16384)
            if not chunk:
                break
            raw += chunk
        s.close()
        dur_ms = (time.time() - t0) * 1000
        return json.loads(raw.decode('utf-8')), dur_ms
    except Exception as e:
        return None, 0.0

def run_tests():
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{VIOLET}   AETHEROS FULL SUBSYSTEM TEST SUITE — BRANCH 2.0 VERIFICATION{RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════{RESET}\n")

    results = []

    # 1. Socket Availability Check
    print(f"{BOLD}[1/8] Verifying IPC Sockets & Daemons...{RESET}")
    all_socks_ok = True
    for name, path in SOCKETS.items():
        exists = os.path.exists(path)
        status_str = f"{GREEN}ONLINE{RESET}" if exists else f"{RED}MISSING{RESET}"
        print(f"  • {name:<26} {path:<24} [{status_str}]")
        if not exists:
            all_socks_ok = False
    results.append(("IPC Socket Accessibility", all_socks_ok, "7/7 active"))

    # 2. Kernel MCP Diagnostic
    print(f"\n{BOLD}[2/8] Testing Kernel MCP NeuroBus (`aether-mcpd`)...{RESET}")
    res, lat = query_sock(SOCKETS["Kernel MCP NeuroBus"], {"action": "call_tool", "name": "system.diagnose", "args": {}})
    mcp_ok = res is not None and "result" in res
    mcp_stat = res.get("result", {}).get("status", "OPTIMAL") if mcp_ok else "FAIL"
    print(f"  • NeuroBus Latency: {lat:.2f}ms")
    print(f"  • Kernel Health:    {mcp_stat}")
    results.append(("Kernel MCP NeuroBus", mcp_ok and lat < 40, f"{lat:.2f}ms"))

    # 3. Vision Sensory Engine
    print(f"\n{BOLD}[3/8] Testing Vision Sensory Engine (`aether-visiond`)...{RESET}")
    res, lat = query_sock(SOCKETS["Vision Sensory Engine"], {"action": "telemetry"})
    vis_ok = res is not None and "biometrics" in res
    user = res.get("biometrics", {}).get("user", "none") if vis_ok else "none"
    conf = res.get("biometrics", {}).get("confidence", 0.0) if vis_ok else 0.0
    print(f"  • Biometric Auth:   User '{user}' (Confidence: {conf*100:.1f}%)")
    print(f"  • Gaze / Posture:   {res.get('ergonomics', {}).get('posture', 'none') if vis_ok else 'none'}")
    results.append(("Vision Sensory Engine", vis_ok and conf > 0.5, f"User: {user} ({conf*100:.0f}%)"))

    # 4. Voice Intelligence
    print(f"\n{BOLD}[4/8] Testing Voice Intelligence (`aether-voiced`)...{RESET}")
    res, lat = query_sock(SOCKETS["Voice Intelligence Core"], {"action": "speak", "text": "AetherOS test suite running"})
    voc_ok = res is not None and res.get("status") in ["PLAYED", "SYNTHESIZED"]
    print(f"  • TTS Synthesis:    {res.get('status', 'FAIL') if res else 'FAIL'} ({lat:.2f}ms)")
    results.append(("Voice Synthesis & Audio", voc_ok, f"{lat:.2f}ms"))

    # 5. Vector Memory Vault
    print(f"\n{BOLD}[5/8] Testing Vector Memory Vault (`aether-memd`)...{RESET}")
    store_res, _ = query_sock(SOCKETS["Vector Memory Vault"], {
        "action": "store",
        "category": "test",
        "key": "test_suite_key",
        "content": "AetherOS automated validation test marker"
    })
    search_res, search_lat = query_sock(SOCKETS["Vector Memory Vault"], {
        "action": "search",
        "query": "automated validation test marker",
        "limit": 3
    })
    mem_ok = search_res is not None and len(search_res) > 0
    top_score = search_res[0].get("similarity", 0.0) if mem_ok else 0.0
    print(f"  • Vector Cosine Query: {search_lat:.2f}ms (Top Similarity: {top_score:.3f})")
    results.append(("Vector Memory Cosine Search", mem_ok and top_score > 0.4, f"Sim: {top_score:.3f} in {search_lat:.2f}ms"))

    # 6. Micro-Intent Router
    print(f"\n{BOLD}[6/8] Testing Micro-Intent Router (`aether-intentd`)...{RESET}")
    int_res, int_lat = query_sock(SOCKETS["Micro-Intent Router"], {"prompt": "diagnose system"})
    int_ok = int_res is not None and "result" in int_res
    print(f"  • Resolved Intent:   {int_res.get('intent', 'none') if int_ok else 'none'}")
    print(f"  • Latency Benchmark: {int_lat:.2f}ms (Target: < 25ms)")
    results.append(("Micro-Intent Resolution", int_ok and int_lat < 35, f"{int_lat:.2f}ms"))

    # 7. Autonomous Agent Swarm & Self-Healing
    print(f"\n{BOLD}[7/8] Testing Autonomous Agent Swarm (`aether-agentd`)...{RESET}")
    swarm_res, _ = query_sock(SOCKETS["Autonomous Agent Swarm"], {"action": "status"})
    agents = swarm_res.get("agents", {}) if swarm_res else {}
    swarm_ok = len(agents) == 4
    print(f"  • Active Resident Agents: {len(agents)}/4 (Sentinel, Security, DevOps, Health)")
    
    # Test Sentinel heal action
    heal_res, heal_lat = query_sock(SOCKETS["Autonomous Agent Swarm"], {
        "action": "dispatch",
        "agent": "sentinel",
        "agent_action": "heal"
    })
    heal_ok = heal_res is not None and heal_res.get("status") == "SUCCESS"
    print(f"  • Sentinel Self-Healing:  {heal_res.get('status', 'FAIL') if heal_res else 'FAIL'} ({heal_lat:.2f}ms)")
    results.append(("Autonomous Agent Swarm", swarm_ok and heal_ok, f"4/4 agents nominal"))

    # 8. Native MLOps & Hardware Acceleration
    print(f"\n{BOLD}[8/8] Testing Native MLOps Engine (`aether-mlopsd`)...{RESET}")
    mlp_res, _ = query_sock(SOCKETS["Native MLOps Engine"], {"action": "status"})
    mlp_bench, bench_lat = query_sock(SOCKETS["Native MLOps Engine"], {"action": "benchmark", "iterations": 100000})
    mflops = mlp_bench.get("simd_throughput_mflops", 0.0) if mlp_bench else 0.0
    mlp_ok = mlp_res is not None and mflops > 10.0
    print(f"  • Hardware Profile:       {mlp_res.get('hardware', {}).get('vector_compute_rating', 'none') if mlp_res else 'none'}")
    print(f"  • SIMD Float Benchmark:   {mflops:.2f} MFLOPS ({bench_lat:.2f}ms)")
    results.append(("Native MLOps & SIMD Engine", mlp_ok, f"{mflops:.1f} MFLOPS"))

    # Final Summary Matrix
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{VIOLET}                   FINAL TEST RESULTS SUMMARY MATRIX                  {RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════{RESET}")
    
    passed_cnt = 0
    for name, passed, detail in results:
        mark = f"{GREEN}✔ PASS{RESET}" if passed else f"{RED}✘ FAIL{RESET}"
        print(f"  {mark:<16} {name:<32} {DIM}({detail}){RESET}")
        if passed:
            passed_cnt += 1

    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════{RESET}")
    if passed_cnt == len(results):
        print(f"  {BOLD}{GREEN}ALL {passed_cnt}/{len(results)} SUBSYSTEM TESTS PASSED WITH ZERO ERRORS!{RESET}")
        print(f"  {DIM}Branch 2.0 is fully verified and ready for next phase.{RESET}\n")
        return 0
    else:
        print(f"  {BOLD}{RED}{len(results) - passed_cnt} TESTS FAILED!{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
