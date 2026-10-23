#ifndef SERIAL_H
#define SERIAL_H

#include "types.h"
#include <stdarg.h>

#define COM1 0x3F8

void serial_init(void);
void serial_putc(char c);
void serial_write(const char *str);
void kprintf(const char *format, ...);

#endif // SERIAL_H
