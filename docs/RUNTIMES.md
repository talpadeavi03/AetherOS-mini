# AetherOS Subsystems & Runtime Specifications

AetherOS bridges multiple application execution paradigms without virtual machine overhead (where native containerization/translation is possible) or with hardware-accelerated virtualization when required.

---

## 1. Linux Native Subsystem

- **Formats:** Standard ELF binaries, Flatpak, AppImage, deb/pacman packages.
- **Sandboxing:** Seccomp filtering, Linux namespaces (mnt, pid, net, user, ipc, uts), and cgroups v2 resource quotas.
- **Audio & Video:** PipeWire for ultra-low latency audio/video routing, Wayland protocol native.
- **Desktop Integration:** FreeDesktop `.desktop` entries, XDG base directory specifications.

---

## 2. Android Subsystem (Waydroid + Binder)

- **Architecture:** An LXC container running Android Open Source Project (AOSP) system image sharing the host Linux kernel.
- **IPC Mechanism:** Host Linux kernel compiled with `CONFIG_ANDROID_BINDER_IPC` and `CONFIG_ASHMEM`.
- **Display Server:** Wayland surface passthrough directly from Android's `hwcomposer` to the AetherOS Wayland Compositor.
- **Audio:** Audio HAL routes through PipeWire / PulseAudio pulse sink.
- **Storage:** Host `~/Android` mapped into `/sdcard` of Android container.
- **Lifecycle:** Managed by `aether-runtime` (`waydroid session start` / `stop` / `app launch`).

---

## 3. .NET / Cross-Platform Subsystem

- **Runtime:** .NET CoreCLR (cross-platform, high performance JIT/AOT).
- **Supported Formats:**
  - Standalone `.dll` and `.exe` managed assemblies.
  - Avalonia UI applications (GPU-accelerated Skia rendering on Wayland).
  - .NET MAUI desktop applications.
  - Blazor Desktop web-view applications.
- **Execution:** Transparent invocation via `aether run app.dll` or `aether run app.exe` through `aether-runtime` which detects CLR CLI headers (`BSJB` metadata or `mscoree.dll`).

---

## 4. Windows Compatibility Subsystem (Proton / Wine)

- **Runtime:** Valve's Proton & Wine-GE custom builds.
- **Graphics Translation:**
  - DirectX 9/10/11 -> Vulkan via **DXVK**.
  - DirectX 12 -> Vulkan via **VKD3D-Proton**.
- **Container Isolation:** Per-application or per-bottle `WINEPREFIX` stored in `~/.local/share/aether/bottles/<app-id>`.
- **Virtualization Tier:** For heavy productivity suites (Visual Studio, AutoCAD, Adobe Creative Cloud), AetherOS provides an optional QEMU/KVM Windows VM with Hyper-V enlightenment extensions and VirtIO GPU / WinPR for seamless remote app rendering.

---

## 5. Cloud-Native & Container Subsystem

- **Engines:** Native `containerd` with Docker-compatible CLI and `podman`.
- **Local Kubernetes:** Embedded `k3s` (or kind) pre-configured with local ingress and Flannel CNI.
- **Workloads:** Run server images (`redis`, `postgres`, `ollama`) or desktop GUI containers (`x11docker` / Wayland container socket mounting).
