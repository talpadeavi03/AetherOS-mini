#ifndef PIC_H
#define PIC_H

#include "types.h"

#define PIC1_COMMAND 0x20
#define PIC1_DATA    0x21
#define PIC2_COMMAND 0xA0
#define PIC2_DATA    0xA1

#define PIC_EOI      0x20

void pic_remap(u8 offset1, u8 offset2);
void pic_send_eoi(u8 irq);
void pic_set_mask(u8 irq_line);
void pic_clear_mask(u8 irq_line);

#endif // PIC_H
