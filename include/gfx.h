#ifndef GFX_H
#define GFX_H

#include "types.h"

#define COLOR_ARGB(a, r, g, b) (((u32)(a) << 24) | ((u32)(r) << 16) | ((u32)(g) << 8) | ((u32)(b)))
#define COLOR_RGB(r, g, b)      COLOR_ARGB(255, r, g, b)

// Modern macOS / iOS styled palette
#define COLOR_TRANSPARENT      0x00000000
#define COLOR_MACOS_DARK_BG    COLOR_ARGB(255, 20, 24, 33)
#define COLOR_MACOS_PANEL      COLOR_ARGB(210, 30, 36, 48)
#define COLOR_MACOS_PANEL_HL   COLOR_ARGB(230, 42, 50, 68)
#define COLOR_MACOS_BAR        COLOR_ARGB(220, 16, 20, 28)
#define COLOR_MACOS_DOCK       COLOR_ARGB(190, 24, 28, 38)
#define COLOR_MACOS_BORDER     COLOR_ARGB(120, 255, 255, 255)
#define COLOR_MACOS_TEXT       COLOR_ARGB(255, 240, 244, 250)
#define COLOR_MACOS_TEXT_MUTED COLOR_ARGB(255, 150, 162, 180)
#define COLOR_MACOS_ACCENT     COLOR_ARGB(255, 14, 165, 233)  // Vibrant Cyan / Blue
#define COLOR_MACOS_AI_GLOW    COLOR_ARGB(255, 168, 85, 247)  // Deep Purple AI Glow
#define COLOR_BTN_CLOSE        COLOR_ARGB(255, 255, 95, 87)   // Red
#define COLOR_BTN_MIN          COLOR_ARGB(255, 254, 188, 46)  // Yellow
#define COLOR_BTN_MAX          COLOR_ARGB(255, 40, 200, 64)   // Green

struct surface {
    u32 *pixels;
    s32 width;
    s32 height;
    s32 pitch; // pitch in pixels
};

u32 color_blend(u32 bg, u32 fg);

void gfx_putpixel(struct surface *s, s32 x, s32 y, u32 color);
void gfx_fill_rect(struct surface *s, s32 x, s32 y, s32 w, s32 h, u32 color);
void gfx_draw_rect(struct surface *s, s32 x, s32 y, s32 w, s32 h, u32 color);
void gfx_fill_rounded_rect(struct surface *s, s32 x, s32 y, s32 w, s32 h, s32 r, u32 color);
void gfx_draw_rounded_rect(struct surface *s, s32 x, s32 y, s32 w, s32 h, s32 r, u32 color);
void gfx_fill_circle(struct surface *s, s32 cx, s32 cy, s32 r, u32 color);
void gfx_draw_circle(struct surface *s, s32 cx, s32 cy, s32 r, u32 color);

void gfx_draw_gradient_v(struct surface *s, s32 x, s32 y, s32 w, s32 h, u32 top_color, u32 bottom_color);
void gfx_draw_shadow(struct surface *s, s32 x, s32 y, s32 w, s32 h, s32 r, s32 shadow_size);

void gfx_draw_char(struct surface *s, s32 x, s32 y, char c, u32 fg);
void gfx_draw_string(struct surface *s, s32 x, s32 y, const char *str, u32 fg);

#endif // GFX_H
