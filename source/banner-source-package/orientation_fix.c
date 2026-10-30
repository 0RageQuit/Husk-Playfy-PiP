// SPDX-License-Identifier: GPL-2.0-or-later
// Runtime bridge for the exact Husk 3.1 executable identified by the packaging script.
// Every external address is supplied by the linker script and is PC-relative.
typedef unsigned long u64;
typedef unsigned int u32;
extern void swift_orientation_set(u64 mask, long attempt) __attribute__((swiftcall));
extern void dispatch_async_stub(void *queue, void *block);
extern void *main_queue_got;
extern void *stack_block_got;
extern volatile u64 screen_dimensions;
extern int original_orientation(void *self, const void *args, void *ret);
extern void tl_log_line(const char *line);

struct Descriptor { u64 reserved, size; };
struct RotationBlock {
    void *isa;
    u32 flags, reserved;
    void (*invoke)(struct RotationBlock *);
    const struct Descriptor *descriptor;
    u64 mask;
};
static const struct Descriptor descriptor = {0, sizeof(struct RotationBlock)};
static void rotate_main(struct RotationBlock *block) {
    swift_orientation_set(block->mask, 0);
}
// Android SCREEN_ORIENTATION_* -> UIKit UIInterfaceOrientationMask.
static u64 mask_for(int request) {
    switch (request) {
    case 0: return 16; // landscape (home button to the right)
    case 8: return 8;  // reverse landscape
    case 6: case 11: return 24; // sensor/user landscape
    case 1: case 7: case 12: return 2;
    case 9: return 4;
    case -1: case 2: case 4: case 10: case 13: return 26;
    default: return 0; // no-sensor, behind, locked: preserve existing orientation
    }
}
int compat_orientation(void *self, const void *args, void *ret) {
    int result = original_orientation(self, args, ret);
    int request = *(const int *)args;
    u64 mask = mask_for(request);
    if (!mask) return result;
    // Android Java measures and touch coordinates must use the rotated viewport too.
    // A single aligned 64-bit store prevents readers observing a half-swapped pair.
    u64 size = screen_dimensions;
    u32 width = (u32)size, height = (u32)(size >> 32);
    int landscape = (mask & 24) && !(mask & 6);
    int portrait = (mask & 6) && !(mask & 24);
    if (width && height && ((landscape && width < height) || (portrait && width > height)))
        screen_dimensions = ((u64)width << 32) | height;
    struct RotationBlock block = {
        stack_block_got, 1u << 29, 0, rotate_main, &descriptor, mask
    };
    dispatch_async_stub(main_queue_got, &block);
    tl_log_line("compat: requested player orientation queued on the iOS main thread");
    return result;
}
