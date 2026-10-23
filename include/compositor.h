#ifndef COMPOSITOR_H
#define COMPOSITOR_H

#include "types.h"
#include "gfx.h"
#include "limine.h"

void compositor_init(struct limine_framebuffer *fb);
struct surface *compositor_get_surface(void);
void compositor_swap(void);
void compositor_draw_cursor(s32 x, s32 y);

s32 compositor_get_width(void);
s32 compositor_get_height(void);

#endif // COMPOSITOR_H
