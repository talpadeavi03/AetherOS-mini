#ifndef KEYBOARD_H
#define KEYBOARD_H

#include "types.h"

#define KEY_BACKSPACE 0x08
#define KEY_TAB       0x09
#define KEY_ENTER     0x0A
#define KEY_ESCAPE    0x1B
#define KEY_UP        0x80
#define KEY_DOWN      0x81
#define KEY_LEFT      0x82
#define KEY_RIGHT     0x83

void keyboard_init(void);
bool keyboard_has_char(void);
char keyboard_getchar(void);

#endif // KEYBOARD_H
