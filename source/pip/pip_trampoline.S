.text
.global original_render
original_render:
 sub sp, sp, #0xc0
 b render_continue
.global original_pause
original_pause:
 adrp x8, unity_state_page
 b pause_continue
