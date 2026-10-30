// SPDX-License-Identifier: GPL-2.0-or-later
// Exact-build bridge. The dylib owns all state; this RX cave has no writable globals.
typedef unsigned long uptr;
typedef long long i64;
extern int original_render(void *, const void *, void *);
extern void original_pause(int);
extern void *lookup(void *, const char *);
extern unsigned char gpu_paused;
extern void *audio_queue;
extern void audio_pause(int);
extern void java_touch(int,int,float,float);
// Only the GPU flag is changed directly. Android lifecycle and audio follow playing.
void pip_playback_control(int background, int command) {
    // PiP transport pause is not Android Activity.onPause(). Keep the activity alive.
    if (command == 4) {
        __atomic_store_n(&gpu_paused, 1, __ATOMIC_RELEASE);
        audio_pause(1);
        return;
    }
    // command 2: presentation paused, but consume the live stream silently.
    int playing = command != 0;
    __atomic_store_n(&gpu_paused, (background || !playing) != 0, __ATOMIC_RELEASE);
    audio_pause(!playing);
    java_touch(6, !playing, 0.0f, 0.0f);
    if (command == 3) java_touch(10, 1, 0.0f, 0.0f);
}
int pip_render(void *self, const void *args, void *ret) {
    int ok = original_render(self, args, ret);
    // Native ABI return is bool; jvalue.z is one byte. Both must report success.
    if (ok && *(const unsigned char *)ret) {
        const uptr *frame = (const uptr *)(*(const uptr *)args);
        if (frame && frame[0]) {
            void (*enqueue)(void *,i64,void (*)(int,int),void *) = lookup((void *)-2L,"husk_video_pip_enqueue");
            if (enqueue) enqueue((void *)frame[0], (i64)frame[1], pip_playback_control, audio_queue);
        }
    }
    return ok;
}
void pip_pause(int background) {
    unsigned (*policy)(int) = lookup((void *)-2L,"husk_video_pip_policy");
    unsigned mode = policy ? policy(background) : 0;
    if (!(mode & 1)) { original_pause(background); return; }
    // PiP owns decoding/audio while its layer is active or starting.
    // Never run the Metal/ANGLE presentation loop in the background.
    __atomic_store_n(&gpu_paused, (background || ((mode & 2) && !(mode & 4))) != 0, __ATOMIC_RELEASE);
    if ((mode & 2) && !(mode & 4)) audio_pause(1);
}
