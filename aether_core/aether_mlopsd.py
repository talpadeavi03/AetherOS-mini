#!/usr/bin/env python3
"""
AetherOS Native MLOps & Model Runtime Engine (aether-mlopsd)
Manages the OS-level Model Registry, Hardware Acceleration (AVX2/FMA/Vulkan),
Quantization Profiles, and Multi-Tier Inference Routing.
"""

import os
import sys
import time
import json
import socket
import hashlib
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

MLOPS_SOCKET_PATH = "/run/aether/mlops.sock"
MLOPS_HTTP_PORT = 9096
MODELS_DIR = "/var/lib/aether/models"
REGISTRY_FILE = os.path.join(MODELS_DIR, "registry.json")

# Default Built-In Model Manifests
DEFAULT_REGISTRY = {
    "models": [
        {
            "id": "aether-intent-micro-v1",
            "name": "Aether Micro-Intent Grammar Classifier",
            "tier": "tier_1_grammar",
            "type": "grammar_slm",
            "format": "int8_quantized",
            "size_mb": 24.5,
            "latency_ms": 13.5,
            "accelerator": "CPU-AVX2",
            "status": "LOADED_ACTIVE",
            "context_window": 1024,
            "description": "Deterministic sub-15ms system and compositor intent classifier."
        },
        {
            "id": "aether-vision-bio-v2",
            "name": "Aether Sensory Biometric & Gaze Feature Extractor",
            "tier": "sensory_vision",
            "type": "onnx_vision",
            "format": "fp16",
            "size_mb": 42.0,
            "latency_ms": 22.0,
            "accelerator": "Vulkan/Mesa",
            "status": "LOADED_ACTIVE",
            "context_window": 512,
            "description": "Continuous facial landmark, EAR blink rate, and head pose tracker."
        },
        {
            "id": "aether-vector-embed-v1",
            "name": "Aether Episodic Vector Hash Embedder",
            "tier": "memory_vector",
            "type": "vector_embedding",
            "format": "int8",
            "size_mb": 18.0,
            "latency_ms": 4.2,
            "accelerator": "CPU-AVX2",
            "status": "LOADED_ACTIVE",
            "context_window": 2048,
            "description": "High-speed 128-dimensional cosine vector similarity embedder."
        },
        {
            "id": "aether-reasoning-slm-3b",
            "name": "Aether Cognitive Reasoning SLM (3B)",
            "tier": "tier_2_local_reasoning",
            "type": "gguf_slm",
            "format": "q4_k_m",
            "size_mb": 1850.0,
            "latency_ms": 95.0,
            "accelerator": "CPU-AVX2+FMA",
            "status": "STANDBY",
            "context_window": 8192,
            "description": "Local conversational and systems engineering reasoning model."
        },
        {
            "id": "aether-cloud-deepseek-v3",
            "name": "Cloud Neural Core (DeepSeek / Gemini Pro)",
            "tier": "tier_3_cloud",
            "type": "cloud_gateway",
            "format": "fp16_api",
            "size_mb": 0.0,
            "latency_ms": 380.0,
            "accelerator": "HTTPS Cloud NeuroBus",
            "status": "ONLINE_STANDBY",
            "context_window": 64000,
            "description": "Deep architecture, code synthesis, and multimodal cloud reasoning."
        }
    ],
    "active_models": {
        "intent": "aether-intent-micro-v1",
        "vision": "aether-vision-bio-v2",
        "memory": "aether-vector-embed-v1",
        "reasoning": "aether-reasoning-slm-3b"
    }
}

class MLOpsEngine:
    def __init__(self):
        self.registry = self.load_registry()
        self.hw_profile = self.profile_hardware()
        self.benchmark_history = []
        self.running = True

    def load_registry(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        if os.path.exists(REGISTRY_FILE):
            try:
                with open(REGISTRY_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        # Write default registry
        try:
            with open(REGISTRY_FILE, "w") as f:
                json.dump(DEFAULT_REGISTRY, f, indent=2)
        except Exception:
            pass
        return DEFAULT_REGISTRY

    def save_registry(self):
        try:
            with open(REGISTRY_FILE, "w") as f:
                json.dump(self.registry, f, indent=2)
        except Exception:
            pass

    def profile_hardware(self):
        profile = {
            "cpu_model": "Generic x86_64",
            "simd_extensions": [],
            "vector_compute_rating": "STANDARD_X86",
            "gpu_acceleration": "Mesa Softpipe",
            "gflops_estimate": 32.5
        }
        try:
            if os.path.exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", "r") as f:
                    content = f.read()
                    for line in content.splitlines():
                        if line.startswith("model name"):
                            profile["cpu_model"] = line.split(":")[1].strip()
                            break
                    simd_candidates = ["avx512f", "avx2", "avx", "fma", "sse4_2", "sse4_1", "neon"]
                    found = [ext.upper() for ext in simd_candidates if ext in content.lower()]
                    profile["simd_extensions"] = found
                    if "AVX2" in found and "FMA" in found:
                        profile["vector_compute_rating"] = "HIGH_THROUGHPUT_AVX2"
                        profile["gflops_estimate"] = 128.4
                    elif "AVX" in found:
                        profile["vector_compute_rating"] = "MEDIUM_AVX"
                        profile["gflops_estimate"] = 64.0
        except Exception:
            pass

        # Check GPU / DRM
        if os.path.exists("/dev/dri/card0") or os.path.exists("/dev/dri/renderD128"):
            profile["gpu_acceleration"] = "KMS/DRM Hardware Render Node Available"
        return profile

    def run_benchmark(self, iterations=150000):
        t0 = time.time()
        # Synthetic SIMD float multiplication benchmark
        acc = 1.0001
        for i in range(iterations):
            acc = (acc * 1.000023) - 0.000022
        dur = max(0.0001, time.time() - t0)
        mflops = round((iterations * 2) / (dur * 1e6), 2)

        result = {
            "timestamp": time.time(),
            "duration_ms": round(dur * 1000, 2),
            "simd_throughput_mflops": mflops,
            "rating": "OPTIMAL_FOR_LOCAL_SLM" if mflops > 50 else "MODERATE"
        }
        self.benchmark_history.append(result)
        if len(self.benchmark_history) > 20:
            self.benchmark_history.pop(0)
        return result

    def list_models(self):
        return self.registry.get("models", [])

    def register_model(self, model_info):
        required = ["id", "name", "tier", "format", "size_mb"]
        for field in required:
            if field not in model_info:
                return {"error": f"Missing required field: {field}"}
        
        # Check duplicate
        for m in self.registry["models"]:
            if m["id"] == model_info["id"]:
                return {"error": f"Model {model_info['id']} already exists."}

        model_info["status"] = model_info.get("status", "STANDBY")
        self.registry["models"].append(model_info)
        self.save_registry()
        return {"status": "REGISTERED", "model": model_info}

    def switch_model(self, tier, model_id):
        models = {m["id"]: m for m in self.registry["models"]}
        if model_id not in models:
            return {"error": f"Model ID '{model_id}' not found in registry."}

        if "active_models" not in self.registry:
            self.registry["active_models"] = {}

        self.registry["active_models"][tier] = model_id
        # Set loaded status
        for m in self.registry["models"]:
            if m["id"] == model_id:
                m["status"] = "LOADED_ACTIVE"
        self.save_registry()
        return {"status": "SWITCHED", "tier": tier, "active_model": model_id}

    def get_status(self):
        return {
            "status": "OPTIMAL",
            "hardware": self.hw_profile,
            "total_registered_models": len(self.registry.get("models", [])),
            "active_models": self.registry.get("active_models", {}),
            "last_benchmark": self.benchmark_history[-1] if self.benchmark_history else self.run_benchmark(50000)
        }

engine = MLOpsEngine()

class MLOpsHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/status", "/"]:
            data = engine.get_status()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
        elif self.path == "/models":
            data = engine.list_models()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
        elif self.path == "/hardware":
            data = engine.hw_profile
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            req = json.loads(post_data.decode('utf-8')) if post_data else {}
            if self.path == "/benchmark":
                res = engine.run_benchmark(req.get("iterations", 150000))
            elif self.path == "/register":
                res = engine.register_model(req)
            elif self.path == "/switch":
                res = engine.switch_model(req.get("tier", "intent"), req.get("model_id", ""))
            else:
                res = {"error": "Not Found"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res, indent=2).encode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def log_message(self, format, *args):
        return

def run_unix_socket_server():
    if os.path.exists(MLOPS_SOCKET_PATH):
        try:
            os.remove(MLOPS_SOCKET_PATH)
        except OSError:
            pass

    os.makedirs(os.path.dirname(MLOPS_SOCKET_PATH), exist_ok=True)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(MLOPS_SOCKET_PATH)
    server.listen(10)
    os.chmod(MLOPS_SOCKET_PATH, 0o666)

    while engine.running:
        try:
            conn, _ = server.accept()
            req_data = conn.recv(8192)
            if not req_data:
                conn.close()
                continue
            req = json.loads(req_data.decode('utf-8'))
            action = req.get("action", "status")

            if action == "status":
                resp = engine.get_status()
            elif action == "models":
                resp = engine.list_models()
            elif action == "benchmark":
                resp = engine.run_benchmark(req.get("iterations", 150000))
            elif action == "register":
                resp = engine.register_model(req.get("model", {}))
            elif action == "switch":
                resp = engine.switch_model(req.get("tier", "intent"), req.get("model_id", ""))
            else:
                resp = {"error": f"Unknown action {action}"}

            conn.sendall(json.dumps(resp).encode('utf-8'))
            conn.close()
        except Exception:
            pass

def main():
    print("[AetherOS MLOps Engine] Starting Native Model Registry & Compute Runtime...")
    
    # 1. Start Unix Socket Thread
    sock_thread = threading.Thread(target=run_unix_socket_server, daemon=True)
    sock_thread.start()

    # 2. Start HTTP Server on port 9096
    httpd = HTTPServer(('0.0.0.0', MLOPS_HTTP_PORT), MLOpsHTTPHandler)
    print(f"[AetherOS MLOps Engine] Live HTTP REST API at http://127.0.0.1:{MLOPS_HTTP_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        engine.running = False
        httpd.server_close()
        if os.path.exists(MLOPS_SOCKET_PATH):
            os.remove(MLOPS_SOCKET_PATH)

if __name__ == '__main__':
    main()
