#include "gfx.h"
#include "font.h"

u32 color_blend(u32 bg, u32 fg) {
    u32 a_fg = (fg >> 24) & 0xFF;
    if (a_fg == 0) return bg;
    if (a_fg == 255) return fg;

    u32 r_fg = (fg >> 16) & 0xFF;
    u32 g_fg = (fg >> 8) & 0xFF;
    u32 b_fg = fg & 0xFF;

    u32 a_bg = (bg >> 24) & 0xFF;
    u32 r_bg = (bg >> 16) & 0xFF;
    u32 g_bg = (bg >> 8) & 0xFF;
    u32 b_bg = bg & 0xFF;

    u32 inv_a = 255 - a_fg;
    u32 r_out = (r_fg * a_fg + r_bg * inv_a) / 255;
    u32 g_out = (g_fg * a_fg + g_bg * inv_a) / 255;
    u32 b_out = (b_fg * a_fg + b_bg * inv_a) / 255;
    u32 a_out = a_fg + (a_bg * inv_a) / 255;

    return (a_out << 24) | (r_out << 16) | (g_out << 8) | b_out;
}

void gfx_putpixel(struct surface *s, s32 x, s32 y, u32 color) {
    if (x < 0 || y < 0 || x >= s->width || y >= s->height) return;
    u32 *dst = &s->pixels[y * s->pitch + x];
    u32 alpha = (color >> 24) & 0xFF;
    if (alpha == 255) {
        *dst = color;
    } else if (alpha > 0) {
        *dst = color_blend(*dst, color);
    }
}

void gfx_fill_rect(struct surface *s, s32 x, s32 y, s32 w, s32 h, u32 color) {
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > s->width)  w = s->width - x;
    if (y + h > s->height) h = s->height - y;
    if (w <= 0 || h <= 0) return;

    u32 alpha = (color >> 24) & 0xFF;
    for (s32 j = 0; j < h; j++) {
        u32 *row = &s->pixels[(y + j) * s->pitch + x];
        if (alpha == 255) {
            for (s32 i = 0; i < w; i++) {
                row[i] = color;
            }
        } else {
            for (s32 i = 0; i < w; i++) {
                row[i] = color_blend(row[i], color);
            }
        }
    }
}

void gfx_draw_rect(struct surface *s, s32 x, s32 y, s32 w, s32 h, u32 color) {
    if (w <= 0 || h <= 0) return;
    for (s32 i = 0; i < w; i++) {
        gfx_putpixel(s, x + i, y, color);
        gfx_putpixel(s, x + i, y + h - 1, color);
    }
    for (s32 j = 0; j < h; j++) {
        gfx_putpixel(s, x, y + j, color);
        gfx_putpixel(s, x + w - 1, y + j, color);
    }
}

void gfx_fill_rounded_rect(struct surface *s, s32 x, s32 y, s32 w, s32 h, s32 r, u32 color) {
    if (r <= 0) {
        gfx_fill_rect(s, x, y, w, h, color);
        return;
    }
    if (r * 2 > w) r = w / 2;
    if (r * 2 > h) r = h / 2;

    s32 r2 = r * r;

    // Fill center rectangles
    gfx_fill_rect(s, x + r, y, w - 2 * r, h, color);
    gfx_fill_rect(s, x, y + r, r, h - 2 * r, color);
    gfx_fill_rect(s, x + w - r, y + r, r, h - 2 * r, color);

    // Fill 4 corners
    for (s32 dy = 0; dy < r; dy++) {
        for (s32 dx = 0; dx < r; dx++) {
            s32 ox = r - dx - 1;
            s32 oy = r - dy - 1;
            if (ox * ox + oy * oy <= r2) {
                // Top-Left
                gfx_putpixel(s, x + dx, y + dy, color);
                // Top-Right
                gfx_putpixel(s, x + w - 1 - dx, y + dy, color);
                // Bottom-Left
                gfx_putpixel(s, x + dx, y + h - 1 - dy, color);
                // Bottom-Right
                gfx_putpixel(s, x + w - 1 - dx, y + h - 1 - dy, color);
            }
        }
    }
}

void gfx_draw_rounded_rect(struct surface *s, s32 x, s32 y, s32 w, s32 h, s32 r, u32 color) {
    if (r <= 0) {
        gfx_draw_rect(s, x, y, w, h, color);
        return;
    }
    if (r * 2 > w) r = w / 2;
    if (r * 2 > h) r = h / 2;

    // Horizontal edges
    for (s32 i = x + r; i < x + w - r; i++) {
        gfx_putpixel(s, i, y, color);
        gfx_putpixel(s, i, y + h - 1, color);
    }
    // Vertical edges
    for (s32 j = y + r; j < y + h - r; j++) {
        gfx_putpixel(s, x, j, color);
        gfx_putpixel(s, x + w - 1, j, color);
    }

    // Four corner arcs
    s32 cx[4] = { x + r, x + w - r - 1, x + r, x + w - r - 1 };
    s32 cy[4] = { y + r, y + r, y + h - r - 1, y + h - r - 1 };

    s32 px = 0;
    s32 py = r;
    s32 d = 3 - 2 * r;

    while (py >= px) {
        // Draw 8 octants for the four corners
        gfx_putpixel(s, cx[0] - py, cy[0] - px, color);
        gfx_putpixel(s, cx[0] - px, cy[0] - py, color);

        gfx_putpixel(s, cx[1] + py, cy[1] - px, color);
        gfx_putpixel(s, cx[1] + px, cy[1] - py, color);

        gfx_putpixel(s, cx[2] - py, cy[2] + px, color);
        gfx_putpixel(s, cx[2] - px, cy[2] + py, color);

        gfx_putpixel(s, cx[3] + py, cy[3] + px, color);
        gfx_putpixel(s, cx[3] + px, cy[3] + py, color);

        px++;
        if (d > 0) {
            py--;
            d = d + 4 * (px - py) + 10;
        } else {
            d = d + 4 * px + 6;
        }
    }
}

void gfx_fill_circle(struct surface *s, s32 cx, s32 cy, s32 r, u32 color) {
    if (r <= 0) return;
    s32 r2 = r * r;
    for (s32 dy = -r; dy <= r; dy++) {
        for (s32 dx = -r; dx <= r; dx++) {
            if (dx * dx + dy * dy <= r2) {
                gfx_putpixel(s, cx + dx, cy + dy, color);
            }
        }
    }
}

void gfx_draw_circle(struct surface *s, s32 cx, s32 cy, s32 r, u32 color) {
    s32 x = 0;
    s32 y = r;
    s32 d = 3 - 2 * r;
    while (y >= x) {
        gfx_putpixel(s, cx + x, cy + y, color);
        gfx_putpixel(s, cx - x, cy + y, color);
        gfx_putpixel(s, cx + x, cy - y, color);
        gfx_putpixel(s, cx - x, cy - y, color);
        gfx_putpixel(s, cx + y, cy + x, color);
        gfx_putpixel(s, cx - y, cy + x, color);
        gfx_putpixel(s, cx + y, cy - x, color);
        gfx_putpixel(s, cx - y, cy - x, color);
        x++;
        if (d > 0) {
            y--;
            d = d + 4 * (x - y) + 10;
        } else {
            d = d + 4 * x + 6;
        }
    }
}

void gfx_draw_gradient_v(struct surface *s, s32 x, s32 y, s32 w, s32 h, u32 top_color, u32 bottom_color) {
    if (w <= 0 || h <= 0) return;

    u32 r1 = (top_color >> 16) & 0xFF;
    u32 g1 = (top_color >> 8) & 0xFF;
    u32 b1 = top_color & 0xFF;

    u32 r2 = (bottom_color >> 16) & 0xFF;
    u32 g2 = (bottom_color >> 8) & 0xFF;
    u32 b2 = bottom_color & 0xFF;

    for (s32 j = 0; j < h; j++) {
        u32 r = r1 + ((s32)(r2 - r1) * j) / h;
        u32 g = g1 + ((s32)(g2 - g1) * j) / h;
        u32 b = b1 + ((s32)(b2 - b1) * j) / h;
        u32 color = COLOR_RGB(r, g, b);
        for (s32 i = 0; i < w; i++) {
            gfx_putpixel(s, x + i, y + j, color);
        }
    }
}

void gfx_draw_shadow(struct surface *s, s32 x, s32 y, s32 w, s32 h, s32 r, s32 shadow_size) {
    for (s32 layer = shadow_size; layer >= 1; layer--) {
        u32 alpha = (12 * (shadow_size - layer + 1)) / shadow_size;
        u32 shadow_color = COLOR_ARGB(alpha, 0, 0, 0);
        gfx_fill_rounded_rect(s, x - layer, y - layer + 2, w + 2 * layer, h + 2 * layer + 2, r + layer, shadow_color);
    }
}

void gfx_draw_char(struct surface *s, s32 x, s32 y, char c, u32 fg) {
    if ((u8)c >= 128) return;
    const u8 *glyph = font_8x16[(u8)c];

    for (s32 row = 0; row < FONT_HEIGHT; row++) {
        u8 bits = glyph[row];
        for (s32 col = 0; col < FONT_WIDTH; col++) {
            if (bits & (0x80 >> col)) {
                gfx_putpixel(s, x + col, y + row, fg);
            }
        }
    }
}

void gfx_draw_string(struct surface *s, s32 x, s32 y, const char *str, u32 fg) {
    s32 cur_x = x;
    s32 cur_y = y;

    while (*str) {
        if (*str == '\n') {
            cur_x = x;
            cur_y += FONT_HEIGHT + 2;
        } else if (*str == '\t') {
            cur_x += FONT_WIDTH * 4;
        } else {
            gfx_draw_char(s, cur_x, cur_y, *str, fg);
            cur_x += FONT_WIDTH;
        }
        str++;
    }
}
