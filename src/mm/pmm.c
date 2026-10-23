#include "pmm.h"
#include "string.h"
#include "serial.h"

static u8 *bitmap = NULL;
static size_t bitmap_size = 0;
static size_t total_pages = 0;
static size_t used_pages = 0;
static u64 hhdm = 0;
static u64 total_ram = 0;

static inline void bitmap_set(size_t bit) {
    bitmap[bit / 8] |= (1 << (bit % 8));
}

static inline void bitmap_clear(size_t bit) {
    bitmap[bit / 8] &= ~(1 << (bit % 8));
}

static inline bool bitmap_test(size_t bit) {
    return (bitmap[bit / 8] & (1 << (bit % 8))) != 0;
}

void pmm_init(struct limine_memmap_response *memmap, u64 hhdm_offset) {
    hhdm = hhdm_offset;
    u64 highest_addr = 0;

    for (size_t i = 0; i < memmap->entry_count; i++) {
        struct limine_memmap_entry *entry = memmap->entries[i];
        if (entry->type == LIMINE_MEMMAP_USABLE || entry->type == LIMINE_MEMMAP_BOOTLOADER_RECLAIMABLE) {
            u64 top = entry->base + entry->length;
            if (top > highest_addr) {
                highest_addr = top;
            }
            if (entry->type == LIMINE_MEMMAP_USABLE) {
                total_ram += entry->length;
            }
        }
    }

    total_pages = highest_addr / PAGE_SIZE;
    bitmap_size = (total_pages + 7) / 8;
    size_t bitmap_pages = (bitmap_size + PAGE_SIZE - 1) / PAGE_SIZE;

    // Find a usable region large enough to hold the bitmap
    u64 bitmap_phys = 0;
    for (size_t i = 0; i < memmap->entry_count; i++) {
        struct limine_memmap_entry *entry = memmap->entries[i];
        if (entry->type == LIMINE_MEMMAP_USABLE && entry->length >= bitmap_pages * PAGE_SIZE) {
            bitmap_phys = entry->base;
            break;
        }
    }

    bitmap = (u8 *)(bitmap_phys + hhdm);
    // Initially mark all pages as used
    memset(bitmap, 0xFF, bitmap_size);
    used_pages = total_pages;

    // Mark usable memory regions as free
    for (size_t i = 0; i < memmap->entry_count; i++) {
        struct limine_memmap_entry *entry = memmap->entries[i];
        if (entry->type == LIMINE_MEMMAP_USABLE) {
            size_t start_page = entry->base / PAGE_SIZE;
            size_t count = entry->length / PAGE_SIZE;
            for (size_t p = 0; p < count; p++) {
                bitmap_clear(start_page + p);
                used_pages--;
            }
        }
    }

    // Mark the bitmap's own pages as used
    size_t bm_start = bitmap_phys / PAGE_SIZE;
    for (size_t p = 0; p < bitmap_pages; p++) {
        if (!bitmap_test(bm_start + p)) {
            bitmap_set(bm_start + p);
            used_pages++;
        }
    }

    // Reserve first 1MB (BIOS, IVT, Real mode area)
    size_t low_pages = 0x100000 / PAGE_SIZE;
    for (size_t p = 0; p < low_pages; p++) {
        if (!bitmap_test(p)) {
            bitmap_set(p);
            used_pages++;
        }
    }

    kprintf("[AetherOS] PMM initialized. Total RAM: %llu MB, Free Pages: %llu / %llu\n",
            total_ram / (1024 * 1024), (u64)(total_pages - used_pages), (u64)total_pages);
}

void *pmm_alloc_page(void) {
    for (size_t i = 0; i < total_pages; i++) {
        if (!bitmap_test(i)) {
            bitmap_set(i);
            used_pages++;
            return (void *)(i * PAGE_SIZE);
        }
    }
    kprintf("[AetherOS] PMM Out of Memory!\n");
    return NULL;
}

void *pmm_alloc_pages(size_t count) {
    if (count == 0) return NULL;
    size_t continuous = 0;
    size_t start_page = 0;

    for (size_t i = 0; i < total_pages; i++) {
        if (!bitmap_test(i)) {
            if (continuous == 0) start_page = i;
            continuous++;
            if (continuous == count) {
                for (size_t p = 0; p < count; p++) {
                    bitmap_set(start_page + p);
                }
                used_pages += count;
                return (void *)(start_page * PAGE_SIZE);
            }
        } else {
            continuous = 0;
        }
    }
    kprintf("[AetherOS] PMM Out of contiguous memory for %llu pages!\n", (u64)count);
    return NULL;
}

void pmm_free_page(void *phys_addr) {
    size_t page = (u64)phys_addr / PAGE_SIZE;
    if (page < total_pages && bitmap_test(page)) {
        bitmap_clear(page);
        used_pages--;
    }
}

void pmm_free_pages(void *phys_addr, size_t count) {
    size_t start_page = (u64)phys_addr / PAGE_SIZE;
    for (size_t p = 0; p < count; p++) {
        if (start_page + p < total_pages && bitmap_test(start_page + p)) {
            bitmap_clear(start_page + p);
            used_pages--;
        }
    }
}

u64 pmm_get_total_memory(void) {
    return total_ram;
}

u64 pmm_get_used_memory(void) {
    return (u64)used_pages * PAGE_SIZE;
}

u64 pmm_get_hhdm_offset(void) {
    return hhdm;
}
