#include "serial.h"
#include "io.h"
#include "string.h"

static bool serial_ready = false;

void serial_init(void) {
    outb(COM1 + 1, 0x00);    // Disable interrupts
    outb(COM1 + 3, 0x80);    // Enable DLAB (set baud rate divisor)
    outb(COM1 + 0, 0x03);    // Set divisor to 3 (lo byte) 38400 baud
    outb(COM1 + 1, 0x00);    //                  (hi byte)
    outb(COM1 + 3, 0x03);    // 8 bits, no parity, one stop bit
    outb(COM1 + 2, 0xC7);    // Enable FIFO, clear them, with 14-byte threshold
    outb(COM1 + 4, 0x0B);    // IRQs enabled, RTS/DSR set
    serial_ready = true;
    serial_write("\r\n[AetherOS] Serial COM1 initialized.\r\n");
}

static inline int is_transmit_empty(void) {
    return inb(COM1 + 5) & 0x20;
}

void serial_putc(char c) {
    if (!serial_ready) return;
    while (is_transmit_empty() == 0);
    outb(COM1, (u8)c);
}

void serial_write(const char *str) {
    if (!serial_ready) return;
    while (*str) {
        if (*str == '\n') {
            serial_putc('\r');
        }
        serial_putc(*str++);
    }
}

void kprintf(const char *format, ...) {
    char buf[1024];
    va_list args;
    va_start(args, format);
    vsnprintf(buf, sizeof(buf), format, args);
    va_end(args);
    serial_write(buf);
}
