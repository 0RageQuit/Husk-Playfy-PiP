ENTRY(compat_maps)
original_maps_continue = 0x10009c438;
maps_continue = 0x10009c438;
tl_ld_apk_at = 0x10009b780;
tl_ld_main_apk = 0x10009b588;
tl_log_line = 0x1000a1058;
SECTIONS { . = 0x1005c4140; .text : { *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }
