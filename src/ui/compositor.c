#include "compositor.h"
#include "heap.h"
#include "string.h"
#include "serial.h"

static struct limine_framebuffer *active_fb = NULL;
static struct surface backbuffer;
static u32 *backbuffer_mem = NULL;

// macOS-style crisp arrow cursor (12x19)
// 0: transparent, 1: black border, 2: white interior, 3: shadow
static const u8 cursor_map[19][12] = {
    { 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    { 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    { 1, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    { 1, 2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0 },
    { 1, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0, 0 },
    { 1, 2, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0 },
    { 1, 2, 2, 2, 2, 2, 1, 0, 0, 0, 0, 0 },
    { 1, 2, 2, 2, 2, 2, 2, 1, 0, 0, 0, 0 },
    { 1, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 0 },
    { 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0 },
    { 1, 2, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0 },
    { 1, 2, 2, 1, 2, 2, 1, 0, 0, 0, 0, 0 },
    { 1, 2, 1, 0, 1, 2, 2, 1, 0, 0, 0, 0 },
    { 1, 1, 0, 0, 1, 2, 2, 1, 0, 0, 0, 0 },
    { 1, 0, 0, 0, 0, 1, 2, 2, 1, 0, 0, 0 },
    { 0, 0, 0, 0, 0, 1, 2, 2, 1, 0, 0, 0 },
    { 0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 0, 0 },
    { 0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 0, 0 },
    { 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0 }
};

void compositor_init(struct limine_framebuffer *fb) {
    active_fb = fb;

    backbuffer.width = (s32)fb->width;
    backbuffer.height = (s32)fb->height;
    backbuffer.pitch = (s32)(fb->pitch / (fb->bpp / 8));

    size_t buffer_bytes = (size_t)fb->height * (size_t)fb->pitch;
    backbuffer_mem = (u32 *)kmalloc(buffer_bytes);

    if (!backbuffer_mem) {
        kprintf("[AetherOS] CRITICAL: Failed to allocate compositor backbuffer!\n");
        return;
    }

    backbuffer.pixels = backbuffer_mem;
    memset(backbuffer_mem, 0, buffer_bytes);

    kprintf("[AetherOS] Compositor initialized (%dx%d, %d bpp, pitch: %d).\n",
            backbuffer.width, backbuffer.height, (int)fb->bpp, backbuffer.pitch);
}

struct surface *compositor_get_surface(void) {
    return &backbuffer;
}

s32 compositor_get_width(void) {
    return backbuffer.width;
}

s32 compositor_get_height(void) {
    return backbuffer.height;
}

void compositor_draw_cursor(s32 x, s32 y) {
    for (s32 row = 0; row < 19; row++) {
        for (s32 col = 0; col < 12; col++) {
            u8 pixel = cursor_map[row][col];
            if (pixel == 1) { // Black outline
                gfx_putpixel(&backbuffer, x + col, y + row, COLOR_RGB(20, 20, 20));
            } else if (pixel == 2) { // Crisp white interior
                gfx_putpixel(&backbuffer, x + col, y + row, COLOR_RGB(255, 255, 255));
            }
        }
    }
}

void compositor_swap(void) {
    if (!active_fb || !backbuffer_mem) return;

    u32 *src = backbuffer_mem;
    u32 *dst = (u32 *)active_fb->address;
    size_t count = (size_t)backbuffer.height * (size_t)backbuffer.pitch;

    for (size_t i = 0; i < count; i++) {
        dst[i] = src[i];
    }
}
