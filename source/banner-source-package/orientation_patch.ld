ENTRY(compat_orientation)
orientation_config_page = 0x10061b000;
orientation_continue = 0x10002901c;
screen_dimensions = 0x10061ba68;
main_queue_got = 0x1006015d8;
stack_block_got = 0x1006014d8;
dispatch_async_stub = 0x10046a334;
swift_orientation_set = 0x1001c4a04;
tl_log_line = 0x1000a1058;
SECTIONS { . = 0x1005c5000; .text : { *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }
