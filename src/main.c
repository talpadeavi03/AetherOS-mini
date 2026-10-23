#include "aether.h"
#include "limine.h"
#include "serial.h"
#include "gdt.h"
#include "idt.h"
#include "pmm.h"
#include "heap.h"
#include "timer.h"
#include "keyboard.h"
#include "mouse.h"
#include "compositor.h"
#include "desktop.h"
#include "mcp.h"
#include "slm.h"
#include "io.h"

// Limine protocol requests
__attribute__((used, section(".requests")))
static volatile LIMINE_BASE_REVISION(3);

__attribute__((used, section(".requests_start_marker")))
static volatile LIMINE_REQUESTS_START_MARKER;

__attribute__((used, section(".requests")))
static volatile struct limine_framebuffer_request fb_request = {
    .id = LIMINE_FRAMEBUFFER_REQUEST,
    .revision = 0
};

__attribute__((used, section(".requests")))
static volatile struct limine_hhdm_request hhdm_request = {
    .id = LIMINE_HHDM_REQUEST,
    .revision = 0
};

__attribute__((used, section(".requests")))
static volatile struct limine_memmap_request memmap_request = {
    .id = LIMINE_MEMMAP_REQUEST,
    .revision = 0
};

__attribute__((used, section(".requests_end_marker")))
static volatile LIMINE_REQUESTS_END_MARKER;

static void print_banner(void) {
    kprintf("\n");
    kprintf("  ___     _   _               ___  ____  \n");
    kprintf(" / _ \\___| |_| |__   ___ _ __/ _ \\/ ___| \n");
    kprintf("| |_| / _ \\ __| '_ \\ / _ \\ '__| | | \\___ \\ \n");
    kprintf("|  _  | __/ |_| | | |  __/ |  | |_| |___) |\n");
    kprintf("|_| |_|\\___|\\__|_| |_|\\___|_|   \\___/|____/ \n");
    kprintf("===========================================\n");
    kprintf("  AetherOS AI-Native Operating System v%s\n", AETHER_OS_VERSION);
    kprintf("  Codename: %s  |  Arch: x86_64 Long Mode\n", AETHER_OS_CODENAME);
    kprintf("===========================================\n\n");
}

void kmain(void) {
    // 1. Initialize serial debug output first
    serial_init();
    print_banner();

    // 2. Base revision check
    if (LIMINE_BASE_REVISION_SUPPORTED == false) {
        kprintf("[AetherOS] CRITICAL: Limine base revision not supported!\n");
        for (;;) { cli(); hlt(); }
    }

    // 3. Initialize GDT & TSS
    gdt_init();

    // 4. Initialize IDT & PIC
    idt_init();

    // 5. Verify Bootloader responses
    if (hhdm_request.response == NULL || memmap_request.response == NULL) {
        kprintf("[AetherOS] CRITICAL: Bootloader did not supply HHDM or Memory Map!\n");
        for (;;) { cli(); hlt(); }
    }

    if (fb_request.response == NULL || fb_request.response->framebuffer_count == 0) {
        kprintf("[AetherOS] CRITICAL: No graphical framebuffer provided by bootloader!\n");
        for (;;) { cli(); hlt(); }
    }

    struct limine_framebuffer *fb = fb_request.response->framebuffers[0];
    kprintf("[AetherOS] Framebuffer detected: %llux%llu, %d bpp, pitch: %llu\n",
            fb->width, fb->height, (int)fb->bpp, fb->pitch);

    // 6. Memory Managers (Physical & Heap)
    pmm_init(memmap_request.response, hhdm_request.response->offset);
    heap_init();

    // 7. Core Device Drivers
    timer_init(100);       // 100 Hz PIT timer (10ms ticks)
    keyboard_init();       // PS/2 Keyboard on IRQ 1
    compositor_init(fb);   // High-speed offscreen double buffer
    mouse_init((s32)fb->width, (s32)fb->height); // PS/2 Mouse on IRQ 12

    // 8. AI & MCP Subsystems
    mcp_init();            // Kernel Model Context Protocol Engine
    slm_init();            // Embedded SLM Copilot
    desktop_init();        // macOS / iOS High-Aesthetic Desktop

    // 9. Enable Interrupts
    kprintf("[AetherOS] Enabling CPU hardware interrupts (sti)...\n");
    sti();
    mcp_publish_event("KERNEL", "AetherOS kernel fully online. Entering compositor loop.");

    // 10. Main Desktop Compositor & Event Loop
    for (;;) {
        char key = 0;
        if (keyboard_has_char()) {
            key = keyboard_getchar();
        }

        struct mouse_state m = mouse_get_state();

        // Update UI logic
        desktop_update(m, key);

        // Render backbuffer
        desktop_render();

        // Swap to display
        compositor_swap();

        // Wait for next interrupt (approx 60-100 fps)
        hlt();
    }
}
