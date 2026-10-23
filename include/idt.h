#ifndef IDT_H
#define IDT_H

#include "types.h"

struct interrupt_registers {
    // Pushed by isr.S
    u64 r15, r14, r13, r12, r11, r10, r9, r8;
    u64 rbp, rdi, rsi, rdx, rcx, rbx, rax;
    u64 int_no, err_code;
    // Pushed by CPU on interrupt
    u64 rip, cs, rflags, rsp, ss;
} __attribute__((packed));

struct idt_entry {
    u16 offset_low;
    u16 selector;
    u8  ist;
    u8  type_attr;
    u16 offset_mid;
    u32 offset_high;
    u32 zero;
} __attribute__((packed));

struct idt_ptr {
    u16 limit;
    u64 base;
} __attribute__((packed));

typedef void (*isr_handler_t)(struct interrupt_registers *);

void idt_init(void);
void idt_set_gate(u8 num, u64 base, u16 sel, u8 flags);
void register_interrupt_handler(u8 n, isr_handler_t handler);

#endif // IDT_H
