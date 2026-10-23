#include "heap.h"
#include "pmm.h"
#include "string.h"
#include "serial.h"

#define HEAP_MAGIC 0xAE78E405 // AETHER_OS
#define HEAP_INIT_PAGES 2048  // 8 MB initial heap

struct heap_block {
    u32 magic;
    bool is_free;
    size_t size;
    struct heap_block *next;
    struct heap_block *prev;
} __attribute__((aligned(16)));

static struct heap_block *heap_head = NULL;
static u64 heap_used_bytes = 0;
static u64 heap_total_bytes = 0;

void heap_init(void) {
    void *phys = pmm_alloc_pages(HEAP_INIT_PAGES);
    if (!phys) {
        kprintf("[AetherOS] CRITICAL: Failed to allocate physical pages for heap!\n");
        return;
    }

    u64 hhdm = pmm_get_hhdm_offset();
    heap_head = (struct heap_block *)((u64)phys + hhdm);

    heap_total_bytes = (u64)HEAP_INIT_PAGES * PAGE_SIZE;
    heap_head->magic = HEAP_MAGIC;
    heap_head->is_free = true;
    heap_head->size = heap_total_bytes - sizeof(struct heap_block);
    heap_head->next = NULL;
    heap_head->prev = NULL;

    heap_used_bytes = 0;

    kprintf("[AetherOS] Kernel Heap initialized (%llu MB at 0x%016llx).\n",
            heap_total_bytes / (1024 * 1024), (u64)heap_head);
}

void *kmalloc(size_t size) {
    if (size == 0) return NULL;

    // Align size to 16 bytes
    size = (size + 15) & ~((size_t)15);

    struct heap_block *curr = heap_head;
    while (curr) {
        if (curr->magic != HEAP_MAGIC) {
            kprintf("[AetherOS] HEAP CORRUPTION DETECTED at 0x%016llx!\n", (u64)curr);
            return NULL;
        }

        if (curr->is_free && curr->size >= size) {
            // Check if we can split the block
            if (curr->size >= size + sizeof(struct heap_block) + 16) {
                struct heap_block *new_block = (struct heap_block *)((u8 *)curr + sizeof(struct heap_block) + size);
                new_block->magic = HEAP_MAGIC;
                new_block->is_free = true;
                new_block->size = curr->size - size - sizeof(struct heap_block);
                new_block->next = curr->next;
                new_block->prev = curr;

                if (curr->next) {
                    curr->next->prev = new_block;
                }
                curr->next = new_block;
                curr->size = size;
            }

            curr->is_free = false;
            heap_used_bytes += curr->size;
            return (void *)((u8 *)curr + sizeof(struct heap_block));
        }
        curr = curr->next;
    }

    kprintf("[AetherOS] Kernel Heap: out of memory allocating %llu bytes!\n", (u64)size);
    return NULL;
}

void kfree(void *ptr) {
    if (!ptr) return;

    struct heap_block *block = (struct heap_block *)((u8 *)ptr - sizeof(struct heap_block));
    if (block->magic != HEAP_MAGIC) {
        kprintf("[AetherOS] kfree: invalid magic 0x%x at 0x%016llx!\n", block->magic, (u64)block);
        return;
    }

    if (block->is_free) {
        kprintf("[AetherOS] kfree: double free detected at 0x%016llx!\n", (u64)block);
        return;
    }

    block->is_free = true;
    if (heap_used_bytes >= block->size) {
        heap_used_bytes -= block->size;
    } else {
        heap_used_bytes = 0;
    }

    // Coalesce forward
    if (block->next && block->next->is_free) {
        block->size += sizeof(struct heap_block) + block->next->size;
        block->next = block->next->next;
        if (block->next) {
            block->next->prev = block;
        }
    }

    // Coalesce backward
    if (block->prev && block->prev->is_free) {
        block->prev->size += sizeof(struct heap_block) + block->size;
        block->prev->next = block->next;
        if (block->next) {
            block->next->prev = block->prev;
        }
    }
}

void *kcalloc(size_t num, size_t size) {
    size_t total = num * size;
    void *ptr = kmalloc(total);
    if (ptr) {
        memset(ptr, 0, total);
    }
    return ptr;
}

void *krealloc(void *ptr, size_t new_size) {
    if (!ptr) return kmalloc(new_size);
    if (new_size == 0) {
        kfree(ptr);
        return NULL;
    }

    struct heap_block *block = (struct heap_block *)((u8 *)ptr - sizeof(struct heap_block));
    if (block->magic != HEAP_MAGIC) return NULL;

    if (block->size >= new_size) {
        return ptr;
    }

    void *new_ptr = kmalloc(new_size);
    if (new_ptr) {
        memcpy(new_ptr, ptr, block->size);
        kfree(ptr);
    }
    return new_ptr;
}

u64 heap_get_used_bytes(void) {
    return heap_used_bytes;
}

u64 heap_get_free_bytes(void) {
    return (heap_total_bytes > heap_used_bytes) ? (heap_total_bytes - heap_used_bytes) : 0;
}
