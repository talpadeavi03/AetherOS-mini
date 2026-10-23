#include "idt.h"
#include "pic.h"
#include "string.h"
#include "serial.h"
#include "io.h"

static struct idt_entry idt[256];
static struct idt_ptr idtp;
static isr_handler_t interrupt_handlers[256];

// Extern ISR symbols from isr.S
extern void isr0(void);
extern void isr1(void);
extern void isr2(void);
extern void isr3(void);
extern void isr4(void);
extern void isr5(void);
extern void isr6(void);
extern void isr7(void);
extern void isr8(void);
extern void isr9(void);
extern void isr10(void);
extern void isr11(void);
extern void isr12(void);
extern void isr13(void);
extern void isr14(void);
extern void isr15(void);
extern void isr16(void);
extern void isr17(void);
extern void isr18(void);
extern void isr19(void);
extern void isr20(void);
extern void isr21(void);
extern void isr22(void);
extern void isr23(void);
extern void isr24(void);
extern void isr25(void);
extern void isr26(void);
extern void isr27(void);
extern void isr28(void);
extern void isr29(void);
extern void isr30(void);
extern void isr31(void);

// Extern IRQ symbols from isr.S
extern void irq0(void);
extern void irq1(void);
extern void irq2(void);
extern void irq3(void);
extern void irq4(void);
extern void irq5(void);
extern void irq6(void);
extern void irq7(void);
extern void irq8(void);
extern void irq9(void);
extern void irq10(void);
extern void irq11(void);
extern void irq12(void);
extern void irq13(void);
extern void irq14(void);
extern void irq15(void);

static const char *exception_messages[32] = {
    "Division By Zero",
    "Debug",
    "Non Maskable Interrupt",
    "Breakpoint",
    "Into Detected Overflow",
    "Out of Bounds",
    "Invalid Opcode",
    "No Coprocessor",
    "Double Fault",
    "Coprocessor Segment Overrun",
    "Bad TSS",
    "Segment Not Present",
    "Stack Fault",
    "General Protection Fault",
    "Page Fault",
    "Unknown Interrupt",
    "Coprocessor Fault",
    "Alignment Check",
    "Machine Check",
    "SIMD Floating-Point Exception",
    "Virtualization Exception",
    "Control Protection Exception",
    "Reserved",
    "Reserved",
    "Reserved",
    "Reserved",
    "Reserved",
    "Reserved",
    "Hypervisor Injection Exception",
    "VMM Communication Exception",
    "Security Exception",
    "Reserved"
};

void idt_set_gate(u8 num, u64 base, u16 sel, u8 flags) {
    idt[num].offset_low  = (base & 0xFFFF);
    idt[num].offset_mid  = (base >> 16) & 0xFFFF;
    idt[num].offset_high = (base >> 32) & 0xFFFFFFFF;
    idt[num].selector    = sel;
    idt[num].ist         = 0;
    idt[num].type_attr   = flags;
    idt[num].zero        = 0;
}

void register_interrupt_handler(u8 n, isr_handler_t handler) {
    interrupt_handlers[n] = handler;
}

void isr_handler(struct interrupt_registers *regs) {
    if (interrupt_handlers[regs->int_no] != NULL) {
        interrupt_handlers[regs->int_no](regs);
        return;
    }

    kprintf("\n================ [KERNEL EXCEPTION PANIC] ================\n");
    if (regs->int_no < 32) {
        kprintf("Exception: %s (#%d)  Error Code: 0x%x\n",
                exception_messages[regs->int_no], (int)regs->int_no, (int)regs->err_code);
    } else {
        kprintf("Unhandled Interrupt: %d\n", (int)regs->int_no);
    }
    kprintf("RIP: 0x%016llx  CS: 0x%x  RFLAGS: 0x%016llx\n", regs->rip, (u32)regs->cs, regs->rflags);
    kprintf("RSP: 0x%016llx  SS: 0x%x  RBP: 0x%016llx\n", regs->rsp, (u32)regs->ss, regs->rbp);
    kprintf("RAX: 0x%016llx  RBX: 0x%016llx  RCX: 0x%016llx\n", regs->rax, regs->rbx, regs->rcx);
    kprintf("RDX: 0x%016llx  RSI: 0x%016llx  RDI: 0x%016llx\n", regs->rdx, regs->rsi, regs->rdi);

    if (regs->int_no == 14) { // Page fault
        u64 cr2;
        __asm__ volatile ("mov %%cr2, %0" : "=r"(cr2));
        kprintf("CR2 (Faulting Address): 0x%016llx\n", cr2);
    }
    kprintf("System Halted.\n");
    for (;;) {
        cli();
        hlt();
    }
}

void irq_handler(struct interrupt_registers *regs) {
    if (interrupt_handlers[regs->int_no] != NULL) {
        interrupt_handlers[regs->int_no](regs);
    }

    pic_send_eoi((u8)(regs->int_no - 32));
}

void idt_init(void) {
    memset(idt, 0, sizeof(idt));
    memset(interrupt_handlers, 0, sizeof(interrupt_handlers));

    idtp.limit = sizeof(idt) - 1;
    idtp.base = (u64)&idt;

    // CPU Exceptions
    idt_set_gate(0, (u64)isr0, 0x08, 0x8E);
    idt_set_gate(1, (u64)isr1, 0x08, 0x8E);
    idt_set_gate(2, (u64)isr2, 0x08, 0x8E);
    idt_set_gate(3, (u64)isr3, 0x08, 0x8E);
    idt_set_gate(4, (u64)isr4, 0x08, 0x8E);
    idt_set_gate(5, (u64)isr5, 0x08, 0x8E);
    idt_set_gate(6, (u64)isr6, 0x08, 0x8E);
    idt_set_gate(7, (u64)isr7, 0x08, 0x8E);
    idt_set_gate(8, (u64)isr8, 0x08, 0x8E);
    idt_set_gate(9, (u64)isr9, 0x08, 0x8E);
    idt_set_gate(10, (u64)isr10, 0x08, 0x8E);
    idt_set_gate(11, (u64)isr11, 0x08, 0x8E);
    idt_set_gate(12, (u64)isr12, 0x08, 0x8E);
    idt_set_gate(13, (u64)isr13, 0x08, 0x8E);
    idt_set_gate(14, (u64)isr14, 0x08, 0x8E);
    idt_set_gate(15, (u64)isr15, 0x08, 0x8E);
    idt_set_gate(16, (u64)isr16, 0x08, 0x8E);
    idt_set_gate(17, (u64)isr17, 0x08, 0x8E);
    idt_set_gate(18, (u64)isr18, 0x08, 0x8E);
    idt_set_gate(19, (u64)isr19, 0x08, 0x8E);
    idt_set_gate(20, (u64)isr20, 0x08, 0x8E);
    idt_set_gate(21, (u64)isr21, 0x08, 0x8E);
    idt_set_gate(22, (u64)isr22, 0x08, 0x8E);
    idt_set_gate(23, (u64)isr23, 0x08, 0x8E);
    idt_set_gate(24, (u64)isr24, 0x08, 0x8E);
    idt_set_gate(25, (u64)isr25, 0x08, 0x8E);
    idt_set_gate(26, (u64)isr26, 0x08, 0x8E);
    idt_set_gate(27, (u64)isr27, 0x08, 0x8E);
    idt_set_gate(28, (u64)isr28, 0x08, 0x8E);
    idt_set_gate(29, (u64)isr29, 0x08, 0x8E);
    idt_set_gate(30, (u64)isr30, 0x08, 0x8E);
    idt_set_gate(31, (u64)isr31, 0x08, 0x8E);

    // Remap PIC to 32 (0x20) and 40 (0x28)
    pic_remap(0x20, 0x28);

    // Hardware IRQs
    idt_set_gate(32, (u64)irq0, 0x08, 0x8E);
    idt_set_gate(33, (u64)irq1, 0x08, 0x8E);
    idt_set_gate(34, (u64)irq2, 0x08, 0x8E);
    idt_set_gate(35, (u64)irq3, 0x08, 0x8E);
    idt_set_gate(36, (u64)irq4, 0x08, 0x8E);
    idt_set_gate(37, (u64)irq5, 0x08, 0x8E);
    idt_set_gate(38, (u64)irq6, 0x08, 0x8E);
    idt_set_gate(39, (u64)irq7, 0x08, 0x8E);
    idt_set_gate(40, (u64)irq8, 0x08, 0x8E);
    idt_set_gate(41, (u64)irq9, 0x08, 0x8E);
    idt_set_gate(42, (u64)irq10, 0x08, 0x8E);
    idt_set_gate(43, (u64)irq11, 0x08, 0x8E);
    idt_set_gate(44, (u64)irq12, 0x08, 0x8E);
    idt_set_gate(45, (u64)irq13, 0x08, 0x8E);
    idt_set_gate(46, (u64)irq14, 0x08, 0x8E);
    idt_set_gate(47, (u64)irq15, 0x08, 0x8E);

    __asm__ volatile ("lidt %0" : : "m"(idtp));
    kprintf("[AetherOS] IDT loaded with 256 gates.\n");
}
