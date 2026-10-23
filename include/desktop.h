#ifndef DESKTOP_H
#define DESKTOP_H

#include "types.h"
#include "mouse.h"

void desktop_init(void);
void desktop_render(void);
void desktop_update(struct mouse_state mouse, char key);

#endif // DESKTOP_H
