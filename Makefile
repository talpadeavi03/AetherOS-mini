CC := gcc
LD := ld
CFLAGS := -Wall -Wextra -std=gnu11 -ffreestanding -fno-stack-protector -fno-stack-check \
          -fno-lto -fno-pic -fno-pie -m64 -march=x86-64 -mno-80387 -mno-mmx -mno-sse -mno-sse2 \
          -mno-red-zone -mcmodel=kernel -Iinclude -O2
LDFLAGS := -nostdlib -static -m elf_x86_64 -z max-page-size=0x1000 -z noexecstack -T linker.ld

C_SRCS := $(shell find src -name '*.c')
S_SRCS := $(shell find src -name '*.S')

OBJS := $(C_SRCS:src/%.c=build/%.o) $(S_SRCS:src/%.S=build/%.o)

ISO := aetheros.iso
KERNEL := build/kernel.elf

.PHONY: all clean run run-headless iso

all: $(ISO)

$(KERNEL): $(OBJS) linker.ld
	@mkdir -p $(dir $@)
	$(LD) $(LDFLAGS) $(OBJS) -o $@
	@echo "Linked $@"

build/%.o: src/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

build/%.o: src/%.S
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(ISO): $(KERNEL) limine.conf
	@rm -rf iso_root
	@mkdir -p iso_root/boot/limine iso_root/EFI/BOOT
	@cp $(KERNEL) iso_root/boot/kernel.elf
	@cp limine.conf iso_root/boot/limine/limine.conf
	@cp boot/limine/limine-bios.sys iso_root/boot/limine/
	@cp boot/limine/limine-bios-cd.bin iso_root/boot/limine/
	@cp boot/limine/limine-uefi-cd.bin iso_root/boot/limine/
	@cp boot/limine/BOOTX64.EFI iso_root/EFI/BOOT/BOOTX64.EFI
	@xorriso -as mkisofs -b boot/limine/limine-bios-cd.bin \
		-no-emul-boot -boot-load-size 4 -boot-info-table \
		--efi-boot boot/limine/limine-uefi-cd.bin \
		-efi-boot-part --efi-boot-image --protective-msdos-label \
		iso_root -o $(ISO) 2>/dev/null
	@./boot/limine/limine bios-install $(ISO) 2>/dev/null
	@echo "Generated Bootable Hybrid ISO: $(ISO)"

run: $(ISO)
	qemu-system-x86_64 -cdrom $(ISO) -m 512M -serial stdio -vga std

run-headless: $(ISO)
	qemu-system-x86_64 -cdrom $(ISO) -m 512M -serial stdio -display none

arch-image:
	./scripts/build_arch_image.sh

run-arch: aetheros-mini.img
	qemu-system-x86_64 -drive file=aetheros-mini.img,format=raw -m 1G -smp 2 -serial stdio

run-arch-headless: aetheros-mini.img
	qemu-system-x86_64 -drive file=aetheros-mini.img,format=raw -m 1G -smp 2 -serial stdio -display none

clean:
	rm -rf build iso_root $(ISO)
