use aether_ai_engine::LocalModelEngine;
use colored::*;
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
    let engine = LocalModelEngine::new();

    if args.iter().any(|a| a == "--models" || a == "models") {
        println!("{}", "=========================================================".bright_cyan());
        println!("{}", "  AETHER AI : LOCAL MODEL CATALOG & QUANTIZATION PROFILES ".bright_cyan().bold());
        println!("{}", "=========================================================".bright_cyan());

        for m in engine.list_models() {
            println!(" • {} ({})", m.name.bright_green().bold(), m.parameters.cyan());
            println!("   Quant:     {} ({} MB)", m.quantization.yellow(), m.file_size_mb);
            println!("   Repo:      {}", m.hf_repo.dimmed());
            println!("   Best For:  {}", m.recommended_for.white());
            println!();
        }
        return Ok(());
    }

    let prompt = if args.len() > 1 {
        args[1..].join(" ")
    } else {
        "Show system status across all runtimes".to_string()
    };

    println!("{}", "=========================================================".bright_magenta());
    println!("{}", "  AETHER AI LOCAL INFERENCE & MCP TOOL ORCHESTRATION     ".bright_magenta().bold());
    println!("{}", "=========================================================".bright_magenta());
    println!("Prompt:  \"{}\"", prompt.bright_white());

    let resp = engine.process_prompt(&prompt).await?;
    println!("Thought: {}", resp.thought.dimmed());
    println!("Action:  {} tool calls scheduled", resp.tool_calls.len().to_string().cyan());

    for call in &resp.tool_calls {
        println!("  └─ Calling: {}({})", call.name.bright_yellow(), call.arguments.to_string().white());
    }

    let results = engine.execute_tools(&resp.tool_calls).await;
    for r in results {
        if r.success {
            println!("  ✔ {}", "Success".green());
            println!("{}", serde_json::to_string_pretty(&r.output)?);
        } else {
            println!("  ✘ Failed: {:?}", r.error);
        }
    }

    println!();
    println!("Reply:   {}", resp.reply.bright_cyan());
    Ok(())
}
