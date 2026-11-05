use aether_mcpd::McpServer;
use colored::*;
use std::sync::Arc;
use tokio::io::{self, AsyncBufReadExt, AsyncWriteExt, BufReader};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let args: Vec<String> = std::env::args().collect();
    let server = Arc::new(McpServer::new());

    if args.iter().any(|a| a == "--stdio") {
        // Run as stdio MCP server for direct IDE/AI integration
        let stdin = io::stdin();
        let mut stdout = io::stdout();
        let mut lines = BufReader::new(stdin).lines();

        while let Ok(Some(line)) = lines.next_line().await {
            if let Some(resp) = server.handle_rpc(&line).await {
                stdout.write_all(resp.as_bytes()).await?;
                stdout.write_all(b"\n").await?;
                stdout.flush().await?;
            }
        }
    } else {
        println!("{}", "⚡ Starting AetherOS System MCP Daemon...".bright_cyan().bold());
        println!("Socket: {:?}", aether_core::AetherPaths::mcp_socket_path());
        server.run_socket_daemon().await?;
    }

    Ok(())
}
