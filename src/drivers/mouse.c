#include "mouse.h"
#include "idt.h"
#include "io.h"
#include "pic.h"
#include "serial.h"

#define MOUSE_PORT_DATA    0x60
#define MOUSE_PORT_STATUS  0x64
#define MOUSE_PORT_CMD     0x64

static struct mouse_state cur_mouse = { .x = 512, .y = 384, .left_btn = false, .right_btn = false, .middle_btn = false };
static s32 max_width = 1024;
static s32 max_height = 768;

static u8 mouse_cycle = 0;
static u8 mouse_bytes[3];

static inline void mouse_wait_write(void) {
    u32 timeout = 100000;
    while (timeout--) {
        if ((inb(MOUSE_PORT_STATUS) & 0x02) == 0) return;
    }
}

static inline void mouse_wait_read(void) {
    u32 timeout = 100000;
    while (timeout--) {
        if ((inb(MOUSE_PORT_STATUS) & 0x01) == 1) return;
    }
}

static void mouse_write(u8 val) {
    mouse_wait_write();
    outb(MOUSE_PORT_CMD, 0xD4);
    mouse_wait_write();
    outb(MOUSE_PORT_DATA, val);
}

static u8 mouse_read(void) {
    mouse_wait_read();
    return inb(MOUSE_PORT_DATA);
}

static void mouse_callback(struct interrupt_registers *regs) {
    (void)regs;
    u8 status = inb(MOUSE_PORT_STATUS);
    if (!(status & 0x20)) {
        return; // Not mouse data
    }

    u8 data = inb(MOUSE_PORT_DATA);
    mouse_bytes[mouse_cycle++] = data;

    if (mouse_cycle == 1) {
        // Bit 3 of byte 0 should always be 1 for a valid PS/2 mouse packet
        if (!(mouse_bytes[0] & 0x08)) {
            mouse_cycle = 0;
            return;
        }
    }

    if (mouse_cycle == 3) {
        mouse_cycle = 0;

        u8 flags = mouse_bytes[0];
        s32 dx = (s32)mouse_bytes[1];
        s32 dy = (s32)mouse_bytes[2];

        // Sign extend
        if (flags & 0x10) dx |= 0xFFFFFF00;
        if (flags & 0x20) dy |= 0xFFFFFF00;

        // Discard packet if overflow occurred
        if ((flags & 0x40) || (flags & 0x80)) {
            return;
        }

        cur_mouse.left_btn   = (flags & 0x01) != 0;
        cur_mouse.right_btn  = (flags & 0x02) != 0;
        cur_mouse.middle_btn = (flags & 0x04) != 0;

        cur_mouse.x += dx;
        cur_mouse.y -= dy; // In PS/2 mouse, +dy is upwards

        // Clamp to screen bounds
        if (cur_mouse.x < 0) cur_mouse.x = 0;
        if (cur_mouse.y < 0) cur_mouse.y = 0;
        if (cur_mouse.x >= max_width) cur_mouse.x = max_width - 1;
        if (cur_mouse.y >= max_height) cur_mouse.y = max_height - 1;
    }
}

void mouse_init(s32 screen_w, s32 screen_h) {
    max_width = screen_w;
    max_height = screen_h;
    cur_mouse.x = screen_w / 2;
    cur_mouse.y = screen_h / 2;

    // Enable auxiliary device
    mouse_wait_write();
    outb(MOUSE_PORT_CMD, 0xA8);

    // Read compaq status byte
    mouse_wait_write();
    outb(MOUSE_PORT_CMD, 0x20);
    u8 status = mouse_read();

    // Enable IRQ 12 (bit 1) and enable clock (clear bit 5)
    status |= 0x02;
    status &= ~0x20;

    // Write back compaq status byte
    mouse_wait_write();
    outb(MOUSE_PORT_CMD, 0x60);
    mouse_wait_write();
    outb(MOUSE_PORT_DATA, status);

    // Set default settings
    mouse_write(0xF6);
    mouse_read(); // ACK (0xFA)

    // Enable packet streaming
    mouse_write(0xF4);
    mouse_read(); // ACK (0xFA)

    register_interrupt_handler(44, mouse_callback); // IRQ 12 = 44
    pic_clear_mask(2); // Unmask IRQ 2 (cascade slave PIC)
    pic_clear_mask(12); // Unmask IRQ 12 (mouse)

    kprintf("[AetherOS] PS/2 Mouse driver initialized (%dx%d).\n", screen_w, screen_h);
}

struct mouse_state mouse_get_state(void) {
    return cur_mouse;
}

void mouse_set_bounds(s32 w, s32 h) {
    max_width = w;
    max_height = h;
}
