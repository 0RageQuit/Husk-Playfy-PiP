// SPDX-License-Identifier: GPL-2.0-or-later
// Caller holds its platform mutex. One waiting frame and one scheduled drain maximum.
#ifndef HUSK_FRAME_MAILBOX_H
#define HUSK_FRAME_MAILBOX_H
struct HuskFrameMailbox { void *pending; unsigned queued; };
static inline void *husk_frame_offer(struct HuskFrameMailbox *m, void *pixel, int *schedule) {
    void *old = m->pending; m->pending = pixel;
    *schedule = !m->queued; m->queued = 1;
    return old;
}
static inline void *husk_frame_take(struct HuskFrameMailbox *m) {
    void *pixel = m->pending; m->pending = 0; m->queued = 0;
    return pixel;
}
#endif
