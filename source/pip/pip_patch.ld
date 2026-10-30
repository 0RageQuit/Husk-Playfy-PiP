ENTRY(pip_render)
render_continue = 0x10004b7d0;
pause_continue = 0x1000bc284;
unity_state_page = 0x100872000;
lookup = 0x10046a3b8;
gpu_paused = 0x100620cd1;
audio_queue = 0x100613a50;
audio_pause = 0x1000060d0;
java_touch = 0x10002603c;
SECTIONS { . = 0x1005c5400; .text : { *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }
