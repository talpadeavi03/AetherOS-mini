#ifndef TIMER_H
#define TIMER_H

#include "types.h"

void timer_init(u32 frequency);
u64 timer_get_ticks(void);
u64 timer_get_uptime_ms(void);
void timer_sleep(u64 ms);

#endif // TIMER_H
