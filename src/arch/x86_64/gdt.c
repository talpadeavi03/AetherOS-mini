#include "gdt.h"
#include "string.h"
#include "serial.h"

static struct {
    struct gdt_entry null_desc;       // 0x00
    struct gdt_entry kernel_code;     // 0x08
    struct gdt_entry kernel_data;     // 0x10
    struct gdt_entry user_code;       // 0x18
    struct gdt_entry user_data;       // 0x20
    struct gdt_tss_entry tss_desc;    // 0x28 (16 bytes in long mode)
} __attribute__((packed)) gdt;

static struct tss_entry tss;
static struct gdt_ptr gdtp;
static u8 tss_stack[4096];

static void gdt_set_gate(struct gdt_entry *gate, u32 base, u32 limit, u8 access, u8 gran) {
    gate->base_low = (base & 0xFFFF);
    gate->base_middle = (base >> 16) & 0xFF;
    gate->base_high = (base >> 24) & 0xFF;

    gate->limit_low = (limit & 0xFFFF);
    gate->granularity = ((limit >> 16) & 0x0F) | (gran & 0xF0);
    gate->access = access;
}

static void gdt_set_tss(struct gdt_tss_entry *tss_gate, u64 base, u32 limit) {
    tss_gate->length = limit & 0xFFFF;
    tss_gate->base_low = base & 0xFFFF;
    tss_gate->base_mid = (base >> 16) & 0xFF;
    tss_gate->flags1 = 0x89; // Present, 64-bit TSS available
    tss_gate->flags2 = (limit >> 16) & 0x0F;
    tss_gate->base_high = (base >> 24) & 0xFF;
    tss_gate->base_upper = (base >> 32) & 0xFFFFFFFF;
    tss_gate->reserved = 0;
}

void gdt_init(void) {
    memset(&gdt, 0, sizeof(gdt));
    memset(&tss, 0, sizeof(tss));

    // 0x08: Kernel Code 64 (Execute/Read, DPL 0, Long Mode)
    gdt_set_gate(&gdt.kernel_code, 0, 0xFFFFF, 0x9A, 0xAF);

    // 0x10: Kernel Data 64 (Read/Write, DPL 0)
    gdt_set_gate(&gdt.kernel_data, 0, 0xFFFFF, 0x92, 0xCF);

    // 0x18: User Code 64 (Execute/Read, DPL 3, Long Mode)
    gdt_set_gate(&gdt.user_code, 0, 0xFFFFF, 0xFA, 0xAF);

    // 0x20: User Data 64 (Read/Write, DPL 3)
    gdt_set_gate(&gdt.user_data, 0, 0xFFFFF, 0xF2, 0xCF);

    // TSS setup
    tss.rsp0 = (u64)tss_stack + sizeof(tss_stack);
    tss.iomap_base = sizeof(tss);
    gdt_set_tss(&gdt.tss_desc, (u64)&tss, sizeof(tss) - 1);

    gdtp.limit = sizeof(gdt) - 1;
    gdtp.base = (u64)&gdt;

    // Load GDT
    __asm__ volatile ("lgdt %0" : : "m"(gdtp));

    // Reload CS using far return and data segments
    __asm__ volatile (
        "pushq $0x10\n"
        "movq %%rsp, %%rax\n"
        "addq $8, %%rax\n"
        "pushq %%rax\n"
        "pushfq\n"
        "pushq $0x08\n"
        "leaq 1f(%%rip), %%rax\n"
        "pushq %%rax\n"
        "iretq\n"
        "1:\n"
        "movw $0x10, %%ax\n"
        "movw %%ax, %%ds\n"
        "movw %%ax, %%es\n"
        "movw %%ax, %%fs\n"
        "movw %%ax, %%gs\n"
        "movw %%ax, %%ss\n"
        : : : "rax", "memory"
    );

    // Load TSS register (selector 0x28)
    __asm__ volatile ("ltr %%ax" : : "a"(0x28));

    kprintf("[AetherOS] GDT & TSS initialized (64-bit Long Mode).\n");
}
