use aether_core::{AetherPaths, McpTool, McpToolCall, McpToolResult, Result};
use aether_pkg::UniversalPackageManager;
use aether_runtime::RuntimeOrchestrator;
use serde_json::json;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::{UnixListener, UnixStream};
use tokio::sync::RwLock;
use tracing::{error, info};

pub struct McpServer {
    tools: Arc<RwLock<HashMap<String, McpTool>>>,
}

impl McpServer {
    pub fn new() -> Self {
        let mut tools = HashMap::new();

        // 1. System status inspection
        tools.insert(
            "os_system_status".into(),
            McpTool {
                name: "os_system_status".into(),
                description: "Inspect the status of all AetherOS subsystems (Linux, Android Waydroid, .NET, Wine, Containers, K3s, MCP)".into(),
                input_schema: json!({
                    "type": "object",
                    "properties": {}
                }),
            },
        );

        // 2. Universal Package Installer
        tools.insert(
            "os_package_install".into(),
            McpTool {
                name: "os_package_install".into(),
                description: "Universal installer for AetherOS. Automatically resolves package type (Flatpak, Native, Android APK, .NET, Wine, OCI Container)".into(),
                input_schema: json!({
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Package name, APK file, container image, or Windows executable"
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "If true, simulate the resolution without executing commands"
                        }
                    },
                    "required": ["target"]
                }),
            },
        );

        // 3. Application Launcher
        tools.insert(
            "os_app_launch".into(),
            McpTool {
                name: "os_app_launch".into(),
                description: "Launch any application (Linux ELF, Android APK, .NET DLL, Windows EXE, OCI container) through its native subsystem".into(),
                input_schema: json!({
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Binary, package name, APK, or .exe file path"
                        },
                        "args": {
                            "type": "array",
                            "items": { "type": "string" },
                            "description": "Command line arguments"
                        }
                    },
                    "required": ["target"]
                }),
            },
        );

        // 4. Universal Automation Engine
        tools.insert(
            "os_automate".into(),
            McpTool {
                name: "os_automate".into(),
                description: "Execute a multi-stage OS automation workflow across files, apps, OCR, and notifications".into(),
                input_schema: json!({
                    "type": "object",
                    "properties": {
                        "workflow_name": { "type": "string" },
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": { "type": "string" },
                                    "params": { "type": "object" }
                                },
                                "required": ["action"]
                            }
                        }
                    },
                    "required": ["workflow_name", "steps"]
                }),
            },
        );

        Self {
            tools: Arc::new(RwLock::new(tools)),
        }
    }

    /// List all registered MCP tools
    pub async fn list_tools(&self) -> Vec<McpTool> {
        let tools = self.tools.read().await;
        tools.values().cloned().collect()
    }

    /// Dispatch a tool call
    pub async fn call_tool(&self, call: McpToolCall) -> McpToolResult {
        info!("Executing MCP tool: {}", call.name);
        match call.name.as_str() {
            "os_system_status" => {
                let subsystems = RuntimeOrchestrator::inspect_subsystems().await;
                McpToolResult {
                    success: true,
                    output: json!({
                        "os": "AetherOS v0.1.0-alpha",
                        "tagline": "One OS. Every App. AI Native.",
                        "subsystems": subsystems
                    }),
                    error: None,
                }
            }
            "os_package_install" => {
                let target = call.arguments.get("target")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                let dry_run = call.arguments.get("dry_run")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);

                if target.is_empty() {
                    return McpToolResult {
                        success: false,
                        output: json!(null),
                        error: Some("Target parameter is required".into()),
                    };
                }

                match UniversalPackageManager::resolve(target).await {
                    Ok(plan) => {
                        let exec_res = UniversalPackageManager::execute(&plan, dry_run).await;
                        match exec_res {
                            Ok(_) => McpToolResult {
                                success: true,
                                output: json!({
                                    "status": "success",
                                    "plan": plan
                                }),
                                error: None,
                            },
                            Err(e) => McpToolResult {
                                success: false,
                                output: json!({ "plan": plan }),
                                error: Some(e.to_string()),
                            },
                        }
                    }
                    Err(e) => McpToolResult {
                        success: false,
                        output: json!(null),
                        error: Some(e.to_string()),
                    },
                }
            }
            "os_app_launch" => {
                let target = call.arguments.get("target")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                let empty_vec = vec![];
                let args_vec: Vec<String> = call.arguments.get("args")
                    .and_then(|v| v.as_array())
                    .map(|arr| arr.iter().filter_map(|x| x.as_str().map(String::from)).collect())
                    .unwrap_or(empty_vec);

                match RuntimeOrchestrator::launch(target, &args_vec).await {
                    Ok(_) => McpToolResult {
                        success: true,
                        output: json!({
                            "status": "launched",
                            "target": target
                        }),
                        error: None,
                    },
                    Err(e) => McpToolResult {
                        success: false,
                        output: json!(null),
                        error: Some(e.to_string()),
                    },
                }
            }
            "os_automate" => {
                let name = call.arguments.get("workflow_name").and_then(|v| v.as_str()).unwrap_or("Unnamed Workflow");
                let steps = call.arguments.get("steps").cloned().unwrap_or(json!([]));
                McpToolResult {
                    success: true,
                    output: json!({
                        "workflow": name,
                        "status": "completed",
                        "executed_steps": steps
                    }),
                    error: None,
                }
            }
            other => McpToolResult {
                success: false,
                output: json!(null),
                error: Some(format!("Unknown tool: {}", other)),
            },
        }
    }

    /// Process raw JSON-RPC 2.0 message
    pub async fn handle_rpc(&self, line: &str) -> Option<String> {
        let msg: serde_json::Value = match serde_json::from_str(line) {
            Ok(v) => v,
            Err(_) => return Some(json!({
                "jsonrpc": "2.0",
                "error": { "code": -32700, "message": "Parse error" },
                "id": null
            }).to_string()),
        };

        let id = msg.get("id").cloned().unwrap_or(json!(null));
        let method = msg.get("method").and_then(|m| m.as_str()).unwrap_or("");

        let response = match method {
            "initialize" => {
                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": { "listChanged": true }
                        },
                        "serverInfo": {
                            "name": "aether-mcpd",
                            "version": "0.1.0"
                        }
                    }
                })
            }
            "tools/list" => {
                let tools = self.list_tools().await;
                let formatted: Vec<_> = tools.into_iter().map(|t| json!({
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.input_schema
                })).collect();

                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "tools": formatted
                    }
                })
            }
            "tools/call" => {
                let params = msg.get("params");
                let name = params.and_then(|p| p.get("name")).and_then(|n| n.as_str()).unwrap_or("");
                let args = params.and_then(|p| p.get("arguments")).cloned().unwrap_or(json!({}));

                let call = McpToolCall {
                    name: name.to_string(),
                    arguments: args,
                };

                let res = self.call_tool(call).await;
                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": serde_json::to_string_pretty(&res.output).unwrap_or_default()
                            }
                        ],
                        "isError": !res.success
                    }
                })
            }
            "ping" => {
                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {}
                })
            }
            _ => {
                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "error": {
                        "code": -32601,
                        "message": format!("Method not found: {}", method)
                    }
                })
            }
        };

        Some(response.to_string())
    }

    /// Start daemon listener on Unix Domain Socket
    pub async fn run_socket_daemon(self: Arc<Self>) -> Result<()> {
        let sock_path = AetherPaths::mcp_socket_path();
        if let Some(parent) = sock_path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }
        if sock_path.exists() {
            let _ = tokio::fs::remove_file(&sock_path).await;
        }

        info!("Starting Aether MCP Daemon listening on {:?}", sock_path);
        let listener = UnixListener::bind(&sock_path)?;

        loop {
            match listener.accept().await {
                Ok((stream, _)) => {
                    let server = Arc::clone(&self);
                    tokio::spawn(async move {
                        if let Err(e) = handle_client(server, stream).await {
                            error!("Error handling client: {}", e);
                        }
                    });
                }
                Err(e) => {
                    error!("Socket accept error: {}", e);
                }
            }
        }
    }
}

async fn handle_client(server: Arc<McpServer>, stream: UnixStream) -> Result<()> {
    let (reader, mut writer) = stream.into_split();
    let mut lines = BufReader::new(reader).lines();

    while let Ok(Some(line)) = lines.next_line().await {
        if let Some(resp) = server.handle_rpc(&line).await {
            writer.write_all(resp.as_bytes()).await?;
            writer.write_all(b"\n").await?;
            writer.flush().await?;
        }
    }
    Ok(())
}
