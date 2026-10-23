#include "keyboard.h"
#include "idt.h"
#include "io.h"
#include "pic.h"
#include "serial.h"

#define KBD_BUFFER_SIZE 256
static char kbd_buffer[KBD_BUFFER_SIZE];
static volatile int kbd_head = 0;
static volatile int kbd_tail = 0;

static bool shift_pressed = false;
static bool ctrl_pressed = false;
static bool alt_pressed = false;

static const char scancode_ascii_lower[128] = {
    0,  27, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', '\b',
  '\t', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\n',
    0, /* Ctrl */
   'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '`',
    0, /* Left Shift */
  '\\', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/',
    0, /* Right Shift */
   '*',
    0, /* Alt */
   ' ', /* Space */
    0, /* Caps lock */
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, /* F1-F10 */
    0, /* Num lock */
    0, /* Scroll lock */
    0, /* Home */
    (char)KEY_UP, /* Up arrow */
    0, /* Page Up */
   '-',
    (char)KEY_LEFT, /* Left arrow */
    0,
    (char)KEY_RIGHT, /* Right arrow */
   '+',
    0, /* End */
    (char)KEY_DOWN, /* Down arrow */
    0, /* Page Down */
    0, /* Insert */
    0, /* Delete */
    0, 0, 0,
    0, 0, /* F11, F12 */
    0
};

static const char scancode_ascii_upper[128] = {
    0,  27, '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '\b',
  '\t', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '\n',
    0, /* Ctrl */
   'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"', '~',
    0, /* Left Shift */
   '|', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?',
    0, /* Right Shift */
   '*',
    0, /* Alt */
   ' ', /* Space */
    0, /* Caps lock */
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, /* F1-F10 */
    0, /* Num lock */
    0, /* Scroll lock */
    0, /* Home */
    (char)KEY_UP, /* Up arrow */
    0, /* Page Up */
   '-',
    (char)KEY_LEFT, /* Left arrow */
    0,
    (char)KEY_RIGHT, /* Right arrow */
   '+',
    0, /* End */
    (char)KEY_DOWN, /* Down arrow */
    0, /* Page Down */
    0, /* Insert */
    0, /* Delete */
    0, 0, 0,
    0, 0, /* F11, F12 */
    0
};

static void keyboard_callback(struct interrupt_registers *regs) {
    (void)regs;
    u8 scancode = inb(0x60);

    // Key release has bit 7 set
    if (scancode & 0x80) {
        u8 released = scancode & 0x7F;
        if (released == 0x2A || released == 0x36) {
            shift_pressed = false;
        } else if (released == 0x1D) {
            ctrl_pressed = false;
        } else if (released == 0x38) {
            alt_pressed = false;
        }
        return;
    }

    // Key press
    if (scancode == 0x2A || scancode == 0x36) {
        shift_pressed = true;
        return;
    } else if (scancode == 0x1D) {
        ctrl_pressed = true;
        return;
    } else if (scancode == 0x38) {
        alt_pressed = true;
        return;
    }

    if (scancode < 128) {
        char ch = shift_pressed ? scancode_ascii_upper[scancode] : scancode_ascii_lower[scancode];
        if (ch != 0) {
            int next_head = (kbd_head + 1) % KBD_BUFFER_SIZE;
            if (next_head != kbd_tail) {
                kbd_buffer[kbd_head] = ch;
                kbd_head = next_head;
            }
        }
    }
}

void keyboard_init(void) {
    kbd_head = 0;
    kbd_tail = 0;
    shift_pressed = false;
    ctrl_pressed = false;
    alt_pressed = false;

    register_interrupt_handler(33, keyboard_callback); // IRQ 1 = 33
    pic_clear_mask(1); // Unmask IRQ 1

    kprintf("[AetherOS] PS/2 Keyboard driver initialized.\n");
}

bool keyboard_has_char(void) {
    return kbd_head != kbd_tail;
}

char keyboard_getchar(void) {
    while (!keyboard_has_char()) {
        hlt();
    }
    char ch = kbd_buffer[kbd_tail];
    kbd_tail = (kbd_tail + 1) % KBD_BUFFER_SIZE;
    return ch;
}
