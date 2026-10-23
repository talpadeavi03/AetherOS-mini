#include "timer.h"
#include "idt.h"
#include "io.h"
#include "pic.h"
#include "serial.h"

#define PIT_CHANNEL0_DATA 0x40
#define PIT_COMMAND_REG   0x43
#define PIT_BASE_FREQ     1193182

static volatile u64 timer_ticks = 0;
static u32 timer_freq = 100;

static void timer_callback(struct interrupt_registers *regs) {
    (void)regs;
    timer_ticks++;
}

void timer_init(u32 frequency) {
    timer_freq = frequency;
    u32 divisor = PIT_BASE_FREQ / frequency;

    // Command byte: Channel 0, lobyte/hibyte, Mode 3 (Square Wave Generator), Binary
    outb(PIT_COMMAND_REG, 0x36);
    outb(PIT_CHANNEL0_DATA, (u8)(divisor & 0xFF));
    outb(PIT_CHANNEL0_DATA, (u8)((divisor >> 8) & 0xFF));

    register_interrupt_handler(32, timer_callback); // IRQ 0 = 32
    pic_clear_mask(0); // Unmask IRQ 0

    kprintf("[AetherOS] PIT Timer initialized at %d Hz.\n", frequency);
}

u64 timer_get_ticks(void) {
    return timer_ticks;
}

u64 timer_get_uptime_ms(void) {
    if (timer_freq == 0) return 0;
    return (timer_ticks * 1000) / timer_freq;
}

void timer_sleep(u64 ms) {
    u64 target = timer_get_uptime_ms() + ms;
    while (timer_get_uptime_ms() < target) {
        hlt();
    }
}
