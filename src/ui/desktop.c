#include "desktop.h"
#include "compositor.h"
#include "gfx.h"
#include "font.h"
#include "mcp.h"
#include "slm.h"
#include "timer.h"
#include "pmm.h"
#include "heap.h"
#include "string.h"
#include "keyboard.h"

#define INPUT_MAX 64
static char input_buf[INPUT_MAX] = {0};
static size_t input_len = 0;
static bool last_mouse_left = false;

void desktop_init(void) {
    input_len = 0;
    input_buf[0] = '\0';
    last_mouse_left = false;
    mcp_publish_event("DESKTOP", "macOS-style High-Aesthetic desktop initialized");
}

static void draw_top_bar(struct surface *s, s32 w) {
    // macOS Top Menu Bar (height: 28px)
    gfx_fill_rect(s, 0, 0, w, 28, COLOR_MACOS_BAR);
    gfx_fill_rect(s, 0, 27, w, 1, COLOR_ARGB(60, 255, 255, 255)); // Bottom hairline

    // Aether logo emblem
    gfx_fill_rounded_rect(s, 10, 5, 18, 18, 5, COLOR_MACOS_ACCENT);
    gfx_draw_char(s, 15, 6, 'A', COLOR_RGB(255, 255, 255));

    // Menus
    gfx_draw_string(s, 36, 6, "AetherOS", COLOR_RGB(255, 255, 255));
    gfx_draw_string(s, 114, 6, "NeuroBus", COLOR_MACOS_TEXT_MUTED);
    gfx_draw_string(s, 192, 6, "MCP Tools", COLOR_MACOS_TEXT_MUTED);
    gfx_draw_string(s, 280, 6, "Memory", COLOR_MACOS_TEXT_MUTED);
    gfx_draw_string(s, 344, 6, "Compositor", COLOR_MACOS_TEXT_MUTED);

    // Right status tray
    s32 right_x = w - 340;

    // AI Status Indicator pill
    u64 ticks = timer_get_ticks();
    u32 pulse_color = (ticks % 20 < 10) ? COLOR_MACOS_AI_GLOW : COLOR_ARGB(180, 168, 85, 247);
    gfx_fill_rounded_rect(s, right_x, 4, 118, 20, 10, COLOR_ARGB(60, 168, 85, 247));
    gfx_fill_circle(s, right_x + 10, 14, 4, pulse_color);
    gfx_draw_string(s, right_x + 20, 6, "AI: ONLINE", COLOR_RGB(230, 215, 255));

    // RAM usage badge
    u64 used_mb = pmm_get_used_memory() / (1024 * 1024);
    char ram_str[24];
    snprintf(ram_str, sizeof(ram_str), "RAM: %lluMB", used_mb);
    gfx_draw_string(s, right_x + 130, 6, ram_str, COLOR_MACOS_TEXT_MUTED);

    // Clock
    u64 uptime_s = timer_get_uptime_ms() / 1000;
    u32 hours = (uptime_s / 3600) % 24;
    u32 mins = (uptime_s / 60) % 60;
    u32 secs = uptime_s % 60;
    char time_str[16];
    snprintf(time_str, sizeof(time_str), "%02u:%02u:%02u", hours, mins, secs);
    gfx_draw_string(s, right_x + 230, 6, time_str, COLOR_RGB(240, 244, 250));
}

static void draw_dock(struct surface *s, s32 sw, s32 sh) {
    s32 dock_w = 400;
    s32 dock_h = 56;
    s32 dock_x = (sw - dock_w) / 2;
    s32 dock_y = sh - dock_h - 14;

    // Drop shadow
    gfx_draw_shadow(s, dock_x, dock_y, dock_w, dock_h, 24, 6);

    // Glass pill background
    gfx_fill_rounded_rect(s, dock_x, dock_y, dock_w, dock_h, 24, COLOR_MACOS_DOCK);
    gfx_draw_rounded_rect(s, dock_x, dock_y, dock_w, dock_h, 24, COLOR_ARGB(70, 255, 255, 255));

    // 5 Dock Icons
    u32 colors[5] = {
        COLOR_MACOS_AI_GLOW,
        COLOR_ARGB(255, 59, 130, 246),
        COLOR_ARGB(255, 16, 185, 129),
        COLOR_ARGB(255, 245, 158, 11),
        COLOR_ARGB(255, 100, 116, 139)
    };
    char icons[5] = { '*', '#', '>', '$', '@' };

    for (s32 i = 0; i < 5; i++) {
        s32 ix = dock_x + 28 + i * 72;
        s32 iy = dock_y + 8;

        // Icon rounded square
        gfx_fill_rounded_rect(s, ix, iy, 40, 40, 10, colors[i]);
        gfx_draw_char(s, ix + 16, iy + 12, icons[i], COLOR_RGB(255, 255, 255));

        // Active indicator dot for running apps (first 3)
        if (i < 3) {
            gfx_fill_circle(s, ix + 20, dock_y + dock_h - 4, 2, COLOR_RGB(255, 255, 255));
        }
    }
}

static void draw_ai_copilot_window(struct surface *s, s32 wx, s32 wy, s32 ww, s32 wh) {
    // Window drop shadow
    gfx_draw_shadow(s, wx, wy, ww, wh, 14, 8);

    // Window glass container
    gfx_fill_rounded_rect(s, wx, wy, ww, wh, 14, COLOR_MACOS_PANEL);
    gfx_draw_rounded_rect(s, wx, wy, ww, wh, 14, COLOR_ARGB(80, 255, 255, 255));

    // Window Titlebar
    gfx_fill_rounded_rect(s, wx, wy, ww, 36, 14, COLOR_MACOS_PANEL_HL);
    gfx_fill_rect(s, wx, wy + 22, ww, 14, COLOR_MACOS_PANEL_HL); // Squaring bottom of titlebar
    gfx_fill_rect(s, wx, wy + 35, ww, 1, COLOR_ARGB(50, 255, 255, 255));

    // macOS Traffic Light Buttons
    gfx_fill_circle(s, wx + 18, wy + 18, 6, COLOR_BTN_CLOSE);
    gfx_fill_circle(s, wx + 36, wy + 18, 6, COLOR_BTN_MIN);
    gfx_fill_circle(s, wx + 54, wy + 18, 6, COLOR_BTN_MAX);

    // Window Title
    gfx_draw_string(s, wx + 78, wy + 10, "Aether AI Copilot", COLOR_RGB(255, 255, 255));
    gfx_draw_string(s, wx + 236, wy + 10, "[NeuroBus MCP Connected]", COLOR_MACOS_AI_GLOW);

    // Quick Action Bar
    s32 qy = wy + 44;
    gfx_draw_string(s, wx + 16, qy + 4, "Quick Tools:", COLOR_MACOS_TEXT_MUTED);

    // Pill buttons
    gfx_fill_rounded_rect(s, wx + 116, qy, 96, 22, 6, COLOR_ARGB(100, 59, 130, 246));
    gfx_draw_string(s, wx + 122, qy + 3, "[1] Diagnose", COLOR_RGB(255, 255, 255));

    gfx_fill_rounded_rect(s, wx + 220, qy, 90, 22, 6, COLOR_ARGB(100, 16, 185, 129));
    gfx_draw_string(s, wx + 226, qy + 3, "[2] Compact", COLOR_RGB(255, 255, 255));

    gfx_fill_rounded_rect(s, wx + 318, qy, 88, 22, 6, COLOR_ARGB(100, 168, 85, 247));
    gfx_draw_string(s, wx + 324, qy + 3, "[3] Threads", COLOR_RGB(255, 255, 255));

    gfx_fill_rounded_rect(s, wx + 414, qy, 76, 22, 6, COLOR_ARGB(100, 245, 158, 11));
    gfx_draw_string(s, wx + 420, qy + 3, "[4] Stats", COLOR_RGB(255, 255, 255));

    // Chat History Area
    s32 chat_y = wy + 76;
    size_t count = slm_get_history_count();

    for (size_t i = 0; i < count && i < 5; i++) {
        const struct slm_chat_message *msg = slm_get_history_message(i);
        if (!msg) continue;

        if (msg->is_user) {
            // User message bubble (Right aligned)
            s32 msg_w = (s32)strlen(msg->text) * FONT_WIDTH + 16;
            s32 bx = wx + ww - msg_w - 20;
            gfx_fill_rounded_rect(s, bx, chat_y, msg_w, 24, 8, COLOR_ARGB(180, 14, 165, 233));
            gfx_draw_string(s, bx + 8, chat_y + 4, msg->text, COLOR_RGB(255, 255, 255));
            chat_y += 30;
        } else {
            // AI Copilot message box
            gfx_fill_rounded_rect(s, wx + 16, chat_y, ww - 32, 48, 8, COLOR_ARGB(140, 24, 20, 36));
            gfx_draw_rounded_rect(s, wx + 16, chat_y, ww - 32, 48, 8, COLOR_ARGB(70, 168, 85, 247));
            gfx_draw_string(s, wx + 24, chat_y + 4, "Aether-SLM:", COLOR_MACOS_AI_GLOW);
            gfx_draw_string(s, wx + 24, chat_y + 22, msg->text, COLOR_RGB(240, 244, 250));
            chat_y += 56;
        }
    }

    // Input Bar at bottom of window
    s32 in_y = wy + wh - 48;
    gfx_fill_rounded_rect(s, wx + 16, in_y, ww - 32, 34, 10, COLOR_ARGB(160, 16, 20, 28));
    gfx_draw_rounded_rect(s, wx + 16, in_y, ww - 32, 34, 10, COLOR_ARGB(80, 255, 255, 255));

    gfx_draw_string(s, wx + 26, in_y + 9, "> ", COLOR_MACOS_ACCENT);
    if (input_len > 0) {
        gfx_draw_string(s, wx + 42, in_y + 9, input_buf, COLOR_RGB(255, 255, 255));
    } else {
        gfx_draw_string(s, wx + 42, in_y + 9, "Ask Aether AI or enter an MCP tool...", COLOR_MACOS_TEXT_MUTED);
    }

    // Blinking cursor
    if ((timer_get_ticks() % 10) < 5) {
        s32 cursor_x = wx + 42 + (s32)input_len * FONT_WIDTH;
        gfx_fill_rect(s, cursor_x, in_y + 8, 2, 16, COLOR_MACOS_ACCENT);
    }
}

static void draw_system_monitor_window(struct surface *s, s32 wx, s32 wy, s32 ww, s32 wh) {
    // Window drop shadow
    gfx_draw_shadow(s, wx, wy, ww, wh, 14, 8);

    // Glass container
    gfx_fill_rounded_rect(s, wx, wy, ww, wh, 14, COLOR_MACOS_PANEL);
    gfx_draw_rounded_rect(s, wx, wy, ww, wh, 14, COLOR_ARGB(80, 255, 255, 255));

    // Titlebar
    gfx_fill_rounded_rect(s, wx, wy, ww, 36, 14, COLOR_MACOS_PANEL_HL);
    gfx_fill_rect(s, wx, wy + 22, ww, 14, COLOR_MACOS_PANEL_HL);
    gfx_fill_rect(s, wx, wy + 35, ww, 1, COLOR_ARGB(50, 255, 255, 255));

    // Traffic buttons
    gfx_fill_circle(s, wx + 18, wy + 18, 6, COLOR_BTN_CLOSE);
    gfx_fill_circle(s, wx + 36, wy + 18, 6, COLOR_BTN_MIN);
    gfx_fill_circle(s, wx + 54, wy + 18, 6, COLOR_BTN_MAX);

    gfx_draw_string(s, wx + 78, wy + 10, "NeuroBus Monitor", COLOR_RGB(255, 255, 255));

    s32 cy = wy + 48;

    // RAM Metric
    u64 used_ram = pmm_get_used_memory() / (1024 * 1024);
    u64 total_ram = pmm_get_total_memory() / (1024 * 1024);
    char ram_lbl[48];
    snprintf(ram_lbl, sizeof(ram_lbl), "Physical RAM: %lluMB / %lluMB", used_ram, total_ram);
    gfx_draw_string(s, wx + 16, cy, ram_lbl, COLOR_RGB(240, 244, 250));

    // Progress bar for RAM
    s32 bar_w = ww - 32;
    gfx_fill_rounded_rect(s, wx + 16, cy + 18, bar_w, 10, 5, COLOR_ARGB(120, 16, 20, 28));
    s32 ram_fill = (total_ram > 0) ? (s32)((used_ram * bar_w) / total_ram) : 10;
    if (ram_fill < 12) ram_fill = 12;
    gfx_fill_rounded_rect(s, wx + 16, cy + 18, ram_fill, 10, 5, COLOR_ARGB(255, 14, 165, 233));

    cy += 40;

    // Heap Metric
    u64 used_heap = heap_get_used_bytes() / 1024;
    u64 free_heap = heap_get_free_bytes() / 1024;
    u64 total_heap = used_heap + free_heap;
    char heap_lbl[48];
    snprintf(heap_lbl, sizeof(heap_lbl), "Kernel Heap: %lluKB / %lluKB", used_heap, total_heap);
    gfx_draw_string(s, wx + 16, cy, heap_lbl, COLOR_RGB(240, 244, 250));

    gfx_fill_rounded_rect(s, wx + 16, cy + 18, bar_w, 10, 5, COLOR_ARGB(120, 16, 20, 28));
    s32 heap_fill = (total_heap > 0) ? (s32)((used_heap * bar_w) / total_heap) : 10;
    if (heap_fill < 10) heap_fill = 10;
    gfx_fill_rounded_rect(s, wx + 16, cy + 18, heap_fill, 10, 5, COLOR_ARGB(255, 16, 185, 129));

    cy += 40;

    // MCP Bus Summary
    char mcp_sum[64];
    snprintf(mcp_sum, sizeof(mcp_sum), "MCP Tools: %llu  |  Resources: %llu",
             (u64)mcp_get_tools_count(), (u64)mcp_get_resources_count());
    gfx_draw_string(s, wx + 16, cy, mcp_sum, COLOR_MACOS_AI_GLOW);

    cy += 24;
    gfx_draw_string(s, wx + 16, cy, "NeuroBus Live Telemetry Stream:", COLOR_MACOS_TEXT_MUTED);
    cy += 18;

    // Show recent events
    size_t event_cnt = mcp_get_events_count();
    size_t start = (event_cnt > 5) ? (event_cnt - 5) : 0;

    for (size_t i = start; i < event_cnt; i++) {
        const struct mcp_event *e = mcp_get_event(i);
        if (!e) continue;

        char ev_line[64];
        snprintf(ev_line, sizeof(ev_line), "[%s] %s", e->source, e->message);
        gfx_draw_string(s, wx + 16, cy, ev_line, COLOR_RGB(200, 210, 225));
        cy += 18;
    }
}

void desktop_render(void) {
    struct surface *s = compositor_get_surface();
    s32 sw = compositor_get_width();
    s32 sh = compositor_get_height();

    // 1. Dark Modern Space Wallpaper with subtle blue-purple glow
    gfx_draw_gradient_v(s, 0, 0, sw, sh, COLOR_RGB(16, 20, 32), COLOR_RGB(8, 10, 18));
    // Soft ambient highlight in upper-center
    gfx_fill_circle(s, sw / 2, sh / 3, 260, COLOR_ARGB(24, 79, 70, 229));

    // 2. Windows
    draw_ai_copilot_window(s, 36, 44, 520, 420);
    draw_system_monitor_window(s, 574, 44, 414, 420);

    // 3. Top Menu Bar
    draw_top_bar(s, sw);

    // 4. Floating Dock
    draw_dock(s, sw, sh);

    // 5. Mouse Cursor
    struct mouse_state m = mouse_get_state();
    compositor_draw_cursor(m.x, m.y);
}

void desktop_update(struct mouse_state mouse, char key) {
    // Check quick tool button clicks
    if (mouse.left_btn && !last_mouse_left) {
        // Quick tools are around y: 88 to 110 in the AI copilot window
        if (mouse.y >= 88 && mouse.y <= 110) {
            if (mouse.x >= 152 && mouse.x <= 248) {
                // Diagnose
                char res[512];
                slm_query("diagnose", res, sizeof(res));
            } else if (mouse.x >= 256 && mouse.x <= 346) {
                // Compact
                char res[512];
                slm_query("compact", res, sizeof(res));
            } else if (mouse.x >= 354 && mouse.x <= 442) {
                // Threads
                char res[512];
                slm_query("threads", res, sizeof(res));
            } else if (mouse.x >= 450 && mouse.x <= 526) {
                // Stats
                char res[512];
                slm_query("stats", res, sizeof(res));
            }
        }
    }
    last_mouse_left = mouse.left_btn;

    // Keyboard handling
    if (key != 0) {
        if (key == '\n') {
            if (input_len > 0) {
                char response[512];
                slm_query(input_buf, response, sizeof(response));
                input_len = 0;
                input_buf[0] = '\0';
            }
        } else if (key == '\b') {
            if (input_len > 0) {
                input_len--;
                input_buf[input_len] = '\0';
            }
        } else if (key >= ' ' && key <= '~') {
            if (input_len + 1 < INPUT_MAX) {
                input_buf[input_len++] = key;
                input_buf[input_len] = '\0';
            }
        }
    }
}
