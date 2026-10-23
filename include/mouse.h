#ifndef MOUSE_H
#define MOUSE_H

#include "types.h"

struct mouse_state {
    s32 x;
    s32 y;
    bool left_btn;
    bool right_btn;
    bool middle_btn;
};

void mouse_init(s32 screen_w, s32 screen_h);
struct mouse_state mouse_get_state(void);
void mouse_set_bounds(s32 w, s32 h);

#endif // MOUSE_H
