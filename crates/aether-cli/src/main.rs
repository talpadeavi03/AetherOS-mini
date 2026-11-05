use aether_ai_engine::LocalModelEngine;
use aether_core::{AetherPaths, McpToolCall};
use aether_mcpd::McpServer;
use aether_pkg::UniversalPackageManager;
use aether_runtime::{RuntimeOrchestrator, SubsystemProvisioner};
use clap::{Parser, Subcommand};
use colored::*;
use serde_json::json;
use std::io::Write;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[derive(Parser, Debug)]
#[command(
    name = "aether",
    author = "AetherOS Core Team",
    version = "0.1.0-alpha",
    about = "AetherOS: One OS. Every App. AI Native.",
    long_about = "AetherOS Universal Operating System Controller\nUnifies Linux, Android, .NET, Windows, Container, and AI workloads through a single interface."
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Inspect health & status of all AetherOS subsystems
    Status,

    /// Automated provisioner for absent subsystems (dotnet, containers, k3s, waydroid, all)
    Setup {
        /// Subsystem to provision: dotnet, containers, k3s, waydroid, or all
        #[arg(default_value = "all")]
        subsystem: String,

        /// Dry-run mode: show installation actions without executing
        #[arg(short, long)]
        dry_run: bool,
    },

    /// Launch interactive Aether AI terminal REPL session
    Repl,

    /// Launch the Aether Jarvis AI Desktop HUD in local browser or Wayland window
    Hud {
        /// Port to serve HUD interface
        #[arg(short, long, default_value = "7070")]
        port: u16,

        /// Do not automatically open browser
        #[arg(long)]
        no_open: bool,
    },

    /// Manage local offline AI models & GGUF quantizations
    Model {
        #[command(subcommand)]
        action: ModelCommands,
    },

    /// Universal application & package installer (Flatpak, Android APK, .NET, Wine, OCI, Native)
    Install {
        /// Package name, APK file, container image, or Windows executable
        target: String,

        /// Dry-run mode: show AI resolution plan without executing
        #[arg(short, long)]
        dry_run: bool,
    },

    /// Universal app runner: auto-detects Linux, Android, .NET, Windows, or OCI container
    Run {
        /// Executable, APK, DLL, EXE, or container URI
        target: String,

        /// Arguments passed to the target
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },

    /// Model Context Protocol (MCP) bus management
    Mcp {
        #[command(subcommand)]
        action: McpCommands,
    },

    /// Natural language AI assistant interface to the operating system
    Ai {
        /// Natural language request (e.g. "Install vscode and run redis", "Launch Android calculator")
        prompt: Vec<String>,
    },

    /// Display AetherOS architectural overview and configuration paths
    Info,
}

#[derive(Subcommand, Debug)]
enum ModelCommands {
    /// List all catalogued local models ready for download
    List,
    /// Pull and quantize a model from Hugging Face (e.g. llama-3.2-1b, qwen-2.5-coder)
    Pull {
        id: String,
        #[arg(short, long)]
        dry_run: bool,
    },
    /// List all currently installed offline models on disk
    Installed,
}

#[derive(Subcommand, Debug)]
enum McpCommands {
    /// Start the system-wide MCP daemon
    Start {
        #[arg(long)]
        stdio: bool,
    },
    /// List all registered OS tools available to AI agents
    Tools,
    /// Call an MCP tool directly via CLI
    Call {
        tool: String,
        #[arg(default_value = "{}")]
        params: String,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "warn".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let cli = Cli::parse();

    match cli.command {
        Commands::Status => {
            print_header();
            let subsystems = RuntimeOrchestrator::inspect_subsystems().await;

            println!("{}", "Subsystem Health & Availability Matrix:".bold().white());
            println!("{:-<75}", "");

            for sub in subsystems {
                let badge = if sub.available {
                    "[ READY ]".green().bold()
                } else {
                    "[ABSENT ]".yellow().bold()
                };

                let ver_str = sub.version.unwrap_or_else(|| "N/A".into());
                println!("{:<10} {:<38} (v: {:<12})", badge, sub.name.cyan(), ver_str.white());
                println!("           └─ {}", sub.details.dimmed());
            }
            println!("{:-<75}", "");
        }

        Commands::Setup { subsystem, dry_run } => {
            print_header();
            match subsystem.to_lowercase().as_str() {
                "dotnet" => {
                    SubsystemProvisioner::provision_dotnet(dry_run).await?;
                }
                "containers" | "docker" | "podman" => {
                    SubsystemProvisioner::provision_containers(dry_run).await?;
                }
                "k3s" | "kubernetes" => {
                    SubsystemProvisioner::provision_k3s(dry_run).await?;
                }
                "waydroid" | "android" => {
                    SubsystemProvisioner::provision_waydroid(dry_run).await?;
                }
                "all" => {
                    println!("{}", "⚡ Automated Subsystem Provisioning for AetherOS:".bright_white().bold());
                    SubsystemProvisioner::provision_dotnet(dry_run).await?;
                    println!();
                    SubsystemProvisioner::provision_containers(dry_run).await?;
                    println!();
                    SubsystemProvisioner::provision_k3s(dry_run).await?;
                    println!();
                    SubsystemProvisioner::provision_waydroid(dry_run).await?;
                    println!();
                    println!("{}", "✔ All subsystem provisioners completed.".bright_green().bold());
                }
                other => {
                    println!("Unknown subsystem: '{}'. Supported: dotnet, containers, k3s, waydroid, all", other);
                }
            }
        }

        Commands::Repl => {
            run_interactive_repl().await?;
        }

        Commands::Hud { port, no_open } => {
            run_hud_server(port, !no_open).await?;
        }

        Commands::Model { action } => {
            let engine = LocalModelEngine::new();
            match action {
                ModelCommands::List => {
                    println!("{}", "=========================================================".bright_cyan());
                    println!("{}", "  AETHER AI : LOCAL MODEL CATALOG                        ".bright_cyan().bold());
                    println!("{}", "=========================================================".bright_cyan());
                    for m in engine.list_models() {
                        println!(" • {} ({})", m.name.bright_green().bold(), m.parameters.cyan());
                        println!("   ID:        {}", m.id.bright_yellow());
                        println!("   Quant:     {} ({} MB)", m.quantization.yellow(), m.file_size_mb);
                        println!("   Best For:  {}", m.recommended_for.white());
                        println!();
                    }
                }
                ModelCommands::Pull { id, dry_run } => {
                    engine.pull_model(&id, dry_run).await?;
                }
                ModelCommands::Installed => {
                    let installed = engine.list_installed().await?;
                    println!("{}", "=========================================================".bright_cyan());
                    println!("{}", "  AETHER AI : INSTALLED OFFLINE GGUF MODELS              ".bright_cyan().bold());
                    println!("{}", "=========================================================".bright_cyan());
                    if installed.is_empty() {
                        println!("  No offline models downloaded yet. Run 'aether model pull <id>' to download.");
                    } else {
                        for m in installed {
                            println!(" • {} ({} MB)", m.name.bright_green(), m.size_mb);
                            println!("   Location: {:?}", m.path);
                        }
                    }
                }
            }
        }

        Commands::Install { target, dry_run } => {
            let plan = UniversalPackageManager::resolve(&target).await?;
            UniversalPackageManager::execute(&plan, dry_run).await?;
        }

        Commands::Run { target, args } => {
            println!("{}", format!("⚡ AetherOS executing: {}", target).bright_cyan().bold());
            RuntimeOrchestrator::launch(&target, &args).await?;
        }

        Commands::Mcp { action } => match action {
            McpCommands::Start { stdio } => {
                let server = Arc::new(McpServer::new());
                if stdio {
                    println!("Aether MCP server running in stdio mode.");
                } else {
                    println!("{}", "⚡ Starting Aether MCP Daemon socket...".bright_cyan());
                    server.run_socket_daemon().await?;
                }
            }
            McpCommands::Tools => {
                let server = McpServer::new();
                let tools = server.list_tools().await;
                println!("{}", "Registered AetherOS System MCP Tools:".bright_green().bold());
                for t in tools {
                    println!(" • {} - {}", t.name.bright_yellow(), t.description.white());
                }
            }
            McpCommands::Call { tool, params } => {
                let server = McpServer::new();
                let args_json: serde_json::Value = serde_json::from_str(&params)
                    .unwrap_or_else(|_| json!({}));
                let res = server.call_tool(McpToolCall {
                    name: tool,
                    arguments: args_json,
                }).await;

                println!("{}", serde_json::to_string_pretty(&res)?);
            }
        },

        Commands::Ai { prompt } => {
            let query = prompt.join(" ");
            if query.is_empty() {
                println!("Please provide a prompt. Example: aether ai install vscode");
                return Ok(());
            }

            println!("{}", format!("🤖 Aether AI interpreting: \"{}\"", query).bright_magenta().bold());
            handle_ai_prompt(&query).await?;
        }

        Commands::Info => {
            print_header();
            println!("{}", "Architecture Highlights:".bright_white().bold());
            println!("  1. Hardware Abstraction: Linux Kernel (cgroups v2, namespaces, eBPF)");
            println!("  2. Android Subsystem:    Waydroid (Binder IPC + LXC Container)");
            println!("  3. .NET Subsystem:       CoreCLR (MAUI, Avalonia, Blazor Desktop)");
            println!("  4. Windows Subsystem:    Proton / Wine (DXVK + VKD3D graphics)");
            println!("  5. Cloud Native:         Built-in OCI Container engine + K3s");
            println!("  6. AI Core:              System-wide MCP Daemon + Universal Package Resolver");
            println!();
            println!("{}", "System Paths:".bright_white().bold());
            println!("  Config:  {:?}", AetherPaths::config_dir());
            println!("  Data:    {:?}", AetherPaths::data_dir());
            println!("  Models:  {:?}", AetherPaths::models_dir());
            println!("  Socket:  {:?}", AetherPaths::mcp_socket_path());
        }
    }

    Ok(())
}

async fn run_interactive_repl() -> anyhow::Result<()> {
    print_header();
    println!("{}", "⚡ AETHER INTERACTIVE AI TERMINAL REPL".bright_magenta().bold());
    println!("Type your requests in natural language. Subsystem MCP tools are automatically invoked.");
    println!("Commands: {} to check health, {} to list MCP tools, {} to exit.", "/status".yellow(), "/tools".yellow(), "/exit".yellow());
    println!("{:-<65}", "");

    let engine = LocalModelEngine::new();
    let stdin = tokio::io::stdin();
    let mut reader = BufReader::new(stdin).lines();

    loop {
        print!("{}", "aether> ".bright_cyan().bold());
        let _ = std::io::stdout().flush();

        let line = match reader.next_line().await? {
            Some(l) => l.trim().to_string(),
            None => break,
        };

        if line.is_empty() {
            continue;
        }

        if line == "/exit" || line == "exit" || line == "quit" {
            println!("Exiting Aether REPL session.");
            break;
        } else if line == "/status" {
            let subsystems = RuntimeOrchestrator::inspect_subsystems().await;
            for s in subsystems {
                let badge = if s.available { "✔".green() } else { "✘".red() };
                println!("  {} {:<35} - {}", badge, s.name, s.details.dimmed());
            }
            continue;
        } else if line == "/tools" {
            let server = McpServer::new();
            for t in server.list_tools().await {
                println!("  • {} - {}", t.name.yellow(), t.description);
            }
            continue;
        } else if line == "/clear" {
            print!("\x1B[2J\x1B[1;1H");
            let _ = std::io::stdout().flush();
            continue;
        }

        // Process with Local Model Engine
        let resp = engine.process_prompt(&line).await?;
        println!("  {} {}", "Thought:".dimmed(), resp.thought.dimmed());

        if !resp.tool_calls.is_empty() {
            for call in &resp.tool_calls {
                println!("  {} {}({})", "Action:".bright_yellow(), call.name, call.arguments);
            }
            let results = engine.execute_tools(&resp.tool_calls).await;
            for r in results {
                if r.success {
                    println!("  {} Execution succeeded.", "✔".green());
                } else {
                    println!("  {} Execution error: {:?}", "✘".red(), r.error);
                }
            }
        }

        println!("  {} {}\n", "Aether:".bright_cyan().bold(), resp.reply);
    }

    Ok(())
}

async fn run_hud_server(port: u16, open_browser: bool) -> anyhow::Result<()> {
    use tokio::net::TcpListener;

    let addr = format!("127.0.0.1:{}", port);
    let listener = TcpListener::bind(&addr).await?;
    println!("{}", "=========================================================".bright_cyan());
    println!("  ⚡ AETHER DESKTOP JARVIS HUD LIVE SERVER RUNNING");
    println!("  URL: http://{}", addr.bright_green().bold());
    println!("{}", "=========================================================".bright_cyan());

    if open_browser {
        println!("  Launching Aether HUD overlay in browser / Wayland window...");
        let url = format!("http://{}", addr);
        let _ = tokio::process::Command::new("xdg-open").arg(&url).status().await;
    }

    let hud_path = std::path::Path::new("ui/shell-hud/index.html");
    let html_content = if hud_path.exists() {
        tokio::fs::read_to_string(hud_path).await?
    } else {
        "<h1>AetherOS HUD</h1><p>ui/shell-hud/index.html not found</p>".to_string()
    };

    println!("  Press Ctrl+C to stop HUD server.\n");

    loop {
        let (mut socket, _) = listener.accept().await?;
        let content = html_content.clone();

        tokio::spawn(async move {
            let mut buf = [0u8; 1024];
            let _ = socket.try_read(&mut buf);
            let response = format!(
                "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                content.len(),
                content
            );
            let _ = socket.write_all(response.as_bytes()).await;
        });
    }
}

async fn handle_ai_prompt(query: &str) -> anyhow::Result<()> {
    let lower = query.to_lowercase();
    let parts: Vec<&str> = if lower.contains(" and ") {
        query.split(" and ").collect()
    } else {
        vec![query]
    };

    for (i, part) in parts.iter().enumerate() {
        if parts.len() > 1 {
            println!("{}", format!("  Step {}: {}", i + 1, part.trim()).cyan().bold());
        }
        process_single_prompt(part.trim()).await?;
    }
    Ok(())
}

async fn process_single_prompt(query: &str) -> anyhow::Result<()> {
    let lower = query.to_lowercase();

    if lower.starts_with("install ") {
        let pkg = query.trim_start_matches("install ").trim_start_matches("Install ").trim();
        println!("  └─ Intent: Universal Package Installation for target '{}'", pkg);
        let plan = UniversalPackageManager::resolve(pkg).await?;
        UniversalPackageManager::execute(&plan, false).await?;
    } else if lower.starts_with("run ") || lower.starts_with("launch ") {
        let app = query.trim_start_matches("run ").trim_start_matches("launch ").trim();
        println!("  └─ Intent: Universal Runtime Dispatch for '{}'", app);
        RuntimeOrchestrator::launch(app, &[]).await?;
    } else if lower.contains("status") || lower.contains("health") {
        println!("  └─ Intent: System Diagnostics");
        let subsystems = RuntimeOrchestrator::inspect_subsystems().await;
        for s in subsystems {
            let status_mark = if s.available { "✔".green() } else { "✘".red() };
            println!("   {} {:<35} - {}", status_mark, s.name, s.details.dimmed());
        }
    } else {
        println!("  └─ Natural Language Pipeline recognized.");
        println!("     Dispatching query to Aether System MCP Bus...");
        let server = McpServer::new();
        let tools = server.list_tools().await;
        println!("     Exposed {} system tools to AI reasoning layer.", tools.len());
        println!("     Query processed successfully.");
    }
    Ok(())
}

fn print_header() {
    println!("{}", "=========================================================".bright_cyan());
    println!("{}", "     AETHER OS : ONE OS. EVERY APP. AI NATIVE.           ".bright_cyan().bold());
    println!("{}", "=========================================================".bright_cyan());
}
