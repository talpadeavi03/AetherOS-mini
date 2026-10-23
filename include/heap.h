#ifndef HEAP_H
#define HEAP_H

#include "types.h"

void heap_init(void);
void *kmalloc(size_t size);
void kfree(void *ptr);
void *kcalloc(size_t num, size_t size);
void *krealloc(void *ptr, size_t new_size);

u64 heap_get_used_bytes(void);
u64 heap_get_free_bytes(void);

#endif // HEAP_H
