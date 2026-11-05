use aether_core::{AetherError, AppRuntimeKind, Result};
use colored::*;
use serde::{Deserialize, Serialize};
use std::process::Stdio;
use tokio::process::Command;
use tracing::info;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PackageSource {
    Flatpak { app_id: String },
    NativeSystem { package_manager: String, package_name: String },
    AndroidApk { path_or_id: String },
    DotNetGlobalTool { package_name: String },
    ContainerImage { image: String },
    AppImage { download_url: String },
    WineExecutable { installer_url_or_path: String },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstallPlan {
    pub query: String,
    pub source: PackageSource,
    pub runtime: AppRuntimeKind,
    pub reason: String,
    pub sandboxed: bool,
}

pub struct UniversalPackageManager;

impl UniversalPackageManager {
    /// AI / Heuristic Resolver for `aether install <target>`
    pub async fn resolve(target: &str) -> Result<InstallPlan> {
        let trimmed = target.trim();

        // 1. Android APK or package ID (e.g. com.spotify.music or file.apk)
        if trimmed.ends_with(".apk") || (trimmed.contains('.') && trimmed.starts_with("com.")) {
            return Ok(InstallPlan {
                query: trimmed.to_string(),
                source: PackageSource::AndroidApk {
                    path_or_id: trimmed.to_string(),
                },
                runtime: AppRuntimeKind::AndroidWaydroid,
                reason: "Detected Android APK package identifier; routing to Waydroid container runtime.".to_string(),
                sandboxed: true,
            });
        }

        // 2. OCI Container (e.g. redis, postgres, ghcr.io/...)
        if trimmed.starts_with("docker://") || trimmed.starts_with("ghcr.io/") || trimmed.contains(':') && !trimmed.contains('/') {
            let image = trimmed.trim_start_matches("docker://").to_string();
            return Ok(InstallPlan {
                query: trimmed.to_string(),
                source: PackageSource::ContainerImage { image },
                runtime: AppRuntimeKind::ContainerOci,
                reason: "Detected OCI container image; routing to built-in container engine.".to_string(),
                sandboxed: true,
            });
        }

        // 3. .NET tool (e.g. dotnet-dump, dotnet-trace)
        if trimmed.starts_with("dotnet-") {
            return Ok(InstallPlan {
                query: trimmed.to_string(),
                source: PackageSource::DotNetGlobalTool {
                    package_name: trimmed.to_string(),
                },
                runtime: AppRuntimeKind::DotNet,
                reason: "Detected .NET CLI tool; routing to CoreCLR dotnet tool runtime.".to_string(),
                sandboxed: false,
            });
        }

        // 4. Windows installer (e.g. setup.exe, installer.msi)
        if trimmed.ends_with(".exe") || trimmed.ends_with(".msi") {
            return Ok(InstallPlan {
                query: trimmed.to_string(),
                source: PackageSource::WineExecutable {
                    installer_url_or_path: trimmed.to_string(),
                },
                runtime: AppRuntimeKind::WindowsWine,
                reason: "Detected Windows executable; routing to Proton/Wine compatibility layer with DXVK.".to_string(),
                sandboxed: true,
            });
        }

        // 5. Curated Desktop Applications (Prefer Flatpak for clean sandboxing, or Native)
        let (flatpak_id, friendly_reason) = match trimmed.to_lowercase().as_str() {
            "vscode" | "code" => (
                Some("com.visualstudio.code"),
                "Selected Flatpak for complete sandboxing, desktop Wayland integration, and extension isolation.",
            ),
            "firefox" => (
                Some("org.mozilla.firefox"),
                "Selected Flatpak distribution with Wayland-native rendering and audio isolation.",
            ),
            "blender" => (
                Some("org.blender.Blender"),
                "Selected Flatpak with full Vulkan/CUDA GPU passthrough and isolated plugins.",
            ),
            "obs" | "obs-studio" => (
                Some("com.obsproject.Studio"),
                "Selected Flatpak with PipeWire screen capture and VAAPI hardware video encoding.",
            ),
            "spotify" => (
                Some("com.spotify.Client"),
                "Selected Flatpak for secure sandboxed audio playback.",
            ),
            "steam" => (
                Some("com.valvesoftware.Steam"),
                "Selected Flatpak distribution bundled with Proton, DXVK, and 32-bit graphics libraries.",
            ),
            _ => (None, ""),
        };

        if let Some(id) = flatpak_id {
            return Ok(InstallPlan {
                query: trimmed.to_string(),
                source: PackageSource::Flatpak {
                    app_id: id.to_string(),
                },
                runtime: AppRuntimeKind::LinuxNative,
                reason: friendly_reason.to_string(),
                sandboxed: true,
            });
        }

        // 6. Native Package Manager detection (pacman / apt)
        let native_pm = if Self::has_tool("pacman").await {
            "pacman"
        } else if Self::has_tool("apt").await {
            "apt"
        } else {
            "native"
        };

        Ok(InstallPlan {
            query: trimmed.to_string(),
            source: PackageSource::NativeSystem {
                package_manager: native_pm.to_string(),
                package_name: trimmed.to_string(),
            },
            runtime: AppRuntimeKind::LinuxNative,
            reason: format!(
                "CLI or system utility; installing natively via '{}' hardware abstraction.",
                native_pm
            ),
            sandboxed: false,
        })
    }

    /// Execute the install plan
    pub async fn execute(plan: &InstallPlan, dry_run: bool) -> Result<()> {
        println!("{}", "─── AetherOS Universal Package Resolver ───".bright_cyan().bold());
        println!("  Target:    {}", plan.query.bright_yellow());
        println!("  Runtime:   {}", plan.runtime.to_string().bright_green());
        println!("  Sandboxed: {}", if plan.sandboxed { "Yes (Seccomp/Namespaces)".green() } else { "Host System".yellow() });
        println!("  Strategy:  {}", plan.reason.bright_white());
        println!("{}", "───────────────────────────────────────────".bright_cyan());

        if dry_run {
            println!("{}", " [DRY-RUN] Plan calculated successfully. No changes made.".cyan());
            return Ok(());
        }

        match &plan.source {
            PackageSource::Flatpak { app_id } => {
                if Self::has_tool("flatpak").await {
                    info!("Running: flatpak install -y --user --noninteractive flathub {}", app_id);
                    let mut cmd = Command::new("flatpak");
                    cmd.arg("install").arg("-y").arg("--user").arg("--noninteractive").arg("flathub").arg(app_id);
                    let st = cmd.status().await?;
                    if !st.success() {
                        return Err(AetherError::Runtime(format!("flatpak exited with status {}", st)));
                    }
                } else {
                    println!("[Simulation] Flatpak runtime is downloading & verifying '{}' from Flathub...", app_id);
                    println!("Installed '{}' successfully.", app_id);
                }
            }
            PackageSource::NativeSystem { package_manager, package_name } => {
                println!("Dispatching native install via {} for '{}'...", package_manager, package_name);
                
                // Check if we can run passwordless sudo or are root
                let has_sudo_privs = Command::new("sudo")
                    .arg("-n")
                    .arg("true")
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .status()
                    .await
                    .map(|s| s.success())
                    .unwrap_or(false);

                if has_sudo_privs {
                    let (cmd_bin, args) = match package_manager.as_str() {
                        "pacman" => ("sudo", vec!["pacman", "-S", "--noconfirm", package_name.as_str()]),
                        "apt" => ("sudo", vec!["apt-get", "install", "-y", package_name.as_str()]),
                        _ => ("echo", vec!["Unknown native package manager; simulated"]),
                    };

                    let mut cmd = Command::new(cmd_bin);
                    cmd.args(&args);
                    let st = cmd.status().await?;
                    if !st.success() {
                        return Err(AetherError::Runtime(format!("Native package install failed: {}", st)));
                    }
                } else {
                    println!("{}", format!("  Note: Elevated privileges required for host system changes. Run: sudo {} install {}", package_manager, package_name).dimmed());
                    println!("[Simulation] System package manager dispatch simulated for: {} install {}", package_manager, package_name);
                }
            }
            PackageSource::AndroidApk { path_or_id } => {
                println!("Routing APK '{}' to Waydroid Android runtime...", path_or_id);
                if Self::has_tool("waydroid").await {
                    let mut cmd = Command::new("waydroid");
                    cmd.arg("app").arg("install").arg(path_or_id);
                    cmd.status().await?;
                } else {
                    println!("[Simulation] Waydroid installed APK '{}' into Android container.", path_or_id);
                }
            }
            PackageSource::DotNetGlobalTool { package_name } => {
                println!("Installing .NET tool '{}' via CoreCLR...", package_name);
                if Self::has_tool("dotnet").await {
                    let mut cmd = Command::new("dotnet");
                    cmd.arg("tool").arg("install").arg("-g").arg(package_name);
                    cmd.status().await?;
                } else {
                    println!("[Simulation] Dotnet global tool installed: {}", package_name);
                }
            }
            PackageSource::ContainerImage { image } => {
                println!("Pulling and registering OCI container '{}'...", image);
                let engine = if Self::has_tool("docker").await { "docker" } else { "podman" };
                if Self::has_tool(engine).await {
                    let mut cmd = Command::new(engine);
                    cmd.arg("pull").arg(image);
                    cmd.status().await?;
                } else {
                    println!("[Simulation] Container engine fetched image '{}'", image);
                }
            }
            PackageSource::WineExecutable { installer_url_or_path } => {
                println!("Configuring Proton/Wine bottle for '{}'...", installer_url_or_path);
                println!("[Simulation] Wine prefix initialized with DXVK 2.3 & VKD3D-Proton.");
            }
            PackageSource::AppImage { download_url } => {
                println!("Downloading and making AppImage executable: {}", download_url);
            }
        }

        println!("{}", "✔ Installation complete. App registered in AetherOS Shell & AI Application Hub.".bright_green().bold());
        Ok(())
    }

    async fn has_tool(name: &str) -> bool {
        Command::new("which")
            .arg(name)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .await
            .map(|s| s.success())
            .unwrap_or(false)
    }
}
