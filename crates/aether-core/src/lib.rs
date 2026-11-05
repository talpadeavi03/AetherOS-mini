use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AetherError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("Runtime error: {0}")]
    Runtime(String),

    #[error("Package resolution error: {0}")]
    PackageNotFound(String),

    #[error("Unsupported binary/app format: {0}")]
    UnsupportedFormat(String),

    #[error("Subsystem failure [{subsystem}]: {message}")]
    Subsystem {
        subsystem: String,
        message: String,
    },
}

pub type Result<T> = std::result::Result<T, AetherError>;

/// Supported runtime execution environments in AetherOS
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AppRuntimeKind {
    /// Native Linux ELF binary (system package / Flatpak / AppImage)
    LinuxNative,
    /// Android APK executed via Waydroid container and binder IPC
    AndroidWaydroid,
    /// .NET CLR / CoreCLR runtime (runs .dll, .exe, Avalonia, MAUI, Blazor Desktop)
    DotNet,
    /// Windows binary executed via Wine/Proton compatibility layer
    WindowsWine,
    /// OCI containerized application (Docker / Podman / containerd)
    ContainerOci,
    /// Web / Progressive Web Application
    WebApp,
}

impl std::fmt::Display for AppRuntimeKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::LinuxNative => write!(f, "Linux (Native ELF)"),
            Self::AndroidWaydroid => write!(f, "Android (Waydroid)"),
            Self::DotNet => write!(f, ".NET CoreCLR"),
            Self::WindowsWine => write!(f, "Windows (Wine/Proton)"),
            Self::ContainerOci => write!(f, "OCI Container"),
            Self::WebApp => write!(f, "Web App"),
        }
    }
}

/// Unified App Descriptor across all supported application ecosystems
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppMetadata {
    pub id: String,
    pub name: String,
    pub version: String,
    pub runtime: AppRuntimeKind,
    pub entrypoint: String,
    pub description: Option<String>,
    pub icon: Option<String>,
    pub categories: Vec<String>,
    pub environment: std::collections::HashMap<String, String>,
}

/// System status across all heterogeneous subsystems
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubsystemStatus {
    pub name: String,
    pub available: bool,
    pub version: Option<String>,
    pub details: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AetherSystemStatus {
    pub os_name: String,
    pub kernel_version: String,
    pub subsystems: Vec<SubsystemStatus>,
}

/// Model Context Protocol (MCP) Primitive Models
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpTool {
    pub name: String,
    pub description: String,
    pub input_schema: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpToolCall {
    pub name: String,
    pub arguments: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpToolResult {
    pub success: bool,
    pub output: serde_json::Value,
    pub error: Option<String>,
}

/// System paths configuration for AetherOS
pub struct AetherPaths;

impl AetherPaths {
    pub fn config_dir() -> PathBuf {
        dirs_fallback(".config/aether")
    }

    pub fn data_dir() -> PathBuf {
        dirs_fallback(".local/share/aether")
    }

    pub fn mcp_socket_path() -> PathBuf {
        if let Ok(runtime_dir) = std::env::var("XDG_RUNTIME_DIR") {
            PathBuf::from(runtime_dir).join("aether-mcp.sock")
        } else {
            Self::data_dir().join("aether-mcp.sock")
        }
    }
}

fn dirs_fallback(suffix: &str) -> PathBuf {
    if let Ok(home) = std::env::var("HOME") {
        PathBuf::from(home).join(suffix)
    } else {
        PathBuf::from("/tmp/aether").join(suffix)
    }
}
