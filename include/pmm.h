#ifndef PMM_H
#define PMM_H

#include "types.h"
#include "limine.h"

#define PAGE_SIZE 4096

void pmm_init(struct limine_memmap_response *memmap, u64 hhdm_offset);
void *pmm_alloc_page(void);
void *pmm_alloc_pages(size_t count);
void pmm_free_page(void *phys_addr);
void pmm_free_pages(void *phys_addr, size_t count);

u64 pmm_get_total_memory(void);
u64 pmm_get_used_memory(void);
u64 pmm_get_hhdm_offset(void);

#endif // PMM_H
