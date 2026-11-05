use aether_shell::CompositorBridge;
use colored::*;
use std::sync::Arc;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    println!("{}", "=========================================================".bright_cyan());
    println!("{}", "  AETHER SHELL : WAYLAND COMPOSITOR & AI HUD BRIDGE      ".bright_cyan().bold());
    println!("{}", "=========================================================".bright_cyan());

    let bridge = Arc::new(CompositorBridge::new());
    bridge.refresh_telemetry().await;

    let state = bridge.get_state().await;
    println!("  RAM:           {}/{} MB", state.memory_used_mb, state.memory_total_mb);
    println!("  Waydroid:      {}", if state.waydroid_active { "Active (Connected)".green() } else { "Inactive".yellow() });
    println!("  Tracked Apps:  {} windows", state.windows.len());
    println!("  AI Panel:      Super + Space hotkey ready");

    bridge.run_ipc_server().await?;
    Ok(())
}
