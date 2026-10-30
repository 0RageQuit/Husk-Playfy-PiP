.text
.global original_orientation
original_orientation:
    // The overwritten instruction at _N_setOrientation, then its original body.
    adrp x8, orientation_config_page
    b orientation_continue
