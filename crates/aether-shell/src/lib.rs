use aether_core::{AetherPaths, AppRuntimeKind};
use aether_runtime::RuntimeOrchestrator;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::{UnixListener, UnixStream};
use tokio::sync::RwLock;
use tracing::{error, info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowInfo {
    pub id: String,
    pub title: String,
    pub app_class: String,
    pub runtime: AppRuntimeKind,
    pub workspace: u32,
    pub is_focused: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShellState {
    pub active_window: Option<WindowInfo>,
    pub windows: Vec<WindowInfo>,
    pub ai_panel_visible: bool,
    pub active_workspace: u32,
    pub gpu_utilization_percent: u32,
    pub cpu_utilization_percent: u32,
    pub memory_used_mb: u64,
    pub memory_total_mb: u64,
    pub containers_running: usize,
    pub waydroid_active: bool,
}

pub struct CompositorBridge {
    state: Arc<RwLock<ShellState>>,
}

impl CompositorBridge {
    pub fn new() -> Self {
        let state = ShellState {
            active_window: Some(WindowInfo {
                id: "win-1".into(),
                title: "Aether AI Assistant HUD".into(),
                app_class: "aether.hud".into(),
                runtime: AppRuntimeKind::LinuxNative,
                workspace: 1,
                is_focused: true,
            }),
            windows: vec![
                WindowInfo {
                    id: "win-1".into(),
                    title: "Aether AI Assistant HUD".into(),
                    app_class: "aether.hud".into(),
                    runtime: AppRuntimeKind::LinuxNative,
                    workspace: 1,
                    is_focused: true,
                },
                WindowInfo {
                    id: "win-2".into(),
                    title: "Spotify Mobile".into(),
                    app_class: "waydroid.com.spotify.music".into(),
                    runtime: AppRuntimeKind::AndroidWaydroid,
                    workspace: 2,
                    is_focused: false,
                },
                WindowInfo {
                    id: "win-3".into(),
                    title: "Avalonia UI Studio".into(),
                    app_class: "dotnet.avalonia.studio".into(),
                    runtime: AppRuntimeKind::DotNet,
                    workspace: 1,
                    is_focused: false,
                },
            ],
            ai_panel_visible: false,
            active_workspace: 1,
            gpu_utilization_percent: 18,
            cpu_utilization_percent: 12,
            memory_used_mb: 3200,
            memory_total_mb: 16000,
            containers_running: 2,
            waydroid_active: true,
        };

        Self {
            state: Arc::new(RwLock::new(state)),
        }
    }

    /// Classify window runtime based on Wayland app_id / WM_CLASS
    pub fn classify_runtime(app_id: &str) -> AppRuntimeKind {
        let lower = app_id.to_lowercase();
        if lower.starts_with("waydroid") || lower.contains("android") {
            AppRuntimeKind::AndroidWaydroid
        } else if lower.starts_with("wine") || lower.starts_with("proton") || lower.ends_with(".exe") {
            AppRuntimeKind::WindowsWine
        } else if lower.starts_with("dotnet") || lower.contains("avalonia") {
            AppRuntimeKind::DotNet
        } else if lower.contains("docker") || lower.contains("container") {
            AppRuntimeKind::ContainerOci
        } else {
            AppRuntimeKind::LinuxNative
        }
    }

    /// Toggle floating AI HUD panel visibility
    pub async fn toggle_ai_panel(&self) -> bool {
        let mut st = self.state.write().await;
        st.ai_panel_visible = !st.ai_panel_visible;
        info!("Aether AI HUD panel visibility toggled: {}", st.ai_panel_visible);
        st.ai_panel_visible
    }

    /// Get snapshot of current desktop shell state
    pub async fn get_state(&self) -> ShellState {
        self.state.read().await.clone()
    }

    /// Refresh hardware telemetry (CPU, GPU, Memory)
    pub async fn refresh_telemetry(&self) {
        let mut st = self.state.write().await;

        // Read real /proc/meminfo if available
        if let Ok(meminfo) = tokio::fs::read_to_string("/proc/meminfo").await {
            let mut total_kb = 0u64;
            let mut free_kb = 0u64;
            let mut available_kb = 0u64;

            for line in meminfo.lines() {
                if line.starts_with("MemTotal:") {
                    total_kb = parse_meminfo_val(line);
                } else if line.starts_with("MemFree:") {
                    free_kb = parse_meminfo_val(line);
                } else if line.starts_with("MemAvailable:") {
                    available_kb = parse_meminfo_val(line);
                }
            }

            if total_kb > 0 {
                let avail = if available_kb > 0 { available_kb } else { free_kb };
                st.memory_total_mb = total_kb / 1024;
                st.memory_used_mb = (total_kb.saturating_sub(avail)) / 1024;
            }
        }

        // Subsystems status
        let subs = RuntimeOrchestrator::inspect_subsystems().await;
        st.waydroid_active = subs.iter().any(|s| s.name.contains("Android") && s.available);
    }

    /// Start Wayland Compositor Bridge IPC listener
    pub async fn run_ipc_server(self: Arc<Self>) -> anyhow::Result<()> {
        let sock_path = get_shell_socket_path();
        if let Some(parent) = sock_path.parent() {
            let _ = tokio::fs::create_dir_all(parent).await;
        }
        if sock_path.exists() {
            let _ = tokio::fs::remove_file(&sock_path).await;
        }

        info!("AetherOS Shell Bridge listening on {:?}", sock_path);
        let listener = UnixListener::bind(&sock_path)?;

        loop {
            match listener.accept().await {
                Ok((stream, _)) => {
                    let bridge = Arc::clone(&self);
                    tokio::spawn(async move {
                        if let Err(e) = handle_shell_client(bridge, stream).await {
                            warn!("Shell client disconnected: {}", e);
                        }
                    });
                }
                Err(e) => {
                    error!("Shell bridge accept error: {}", e);
                }
            }
        }
    }
}

fn parse_meminfo_val(line: &str) -> u64 {
    line.split_whitespace()
        .nth(1)
        .and_then(|v| v.parse::<u64>().ok())
        .unwrap_or(0)
}

fn get_shell_socket_path() -> PathBuf {
    if let Ok(runtime_dir) = std::env::var("XDG_RUNTIME_DIR") {
        PathBuf::from(runtime_dir).join("aether-shell.sock")
    } else {
        AetherPaths::data_dir().join("aether-shell.sock")
    }
}

async fn handle_shell_client(bridge: Arc<CompositorBridge>, stream: UnixStream) -> anyhow::Result<()> {
    let (reader, mut writer) = stream.into_split();
    let mut lines = BufReader::new(reader).lines();

    while let Ok(Some(line)) = lines.next_line().await {
        let req: serde_json::Value = serde_json::from_str(&line).unwrap_or(serde_json::json!({}));
        let cmd = req.get("command").and_then(|c| c.as_str()).unwrap_or("");

        let response = match cmd {
            "get_state" => {
                bridge.refresh_telemetry().await;
                let state = bridge.get_state().await;
                serde_json::to_string(&state)?
            }
            "toggle_ai_panel" => {
                let vis = bridge.toggle_ai_panel().await;
                serde_json::json!({ "ai_panel_visible": vis }).to_string()
            }
            "ping" => serde_json::json!({ "status": "ok" }).to_string(),
            _ => serde_json::json!({ "error": "unknown_command" }).to_string(),
        };

        writer.write_all(response.as_bytes()).await?;
        writer.write_all(b"\n").await?;
        writer.flush().await?;
    }
    Ok(())
}
