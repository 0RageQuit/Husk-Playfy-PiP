# Features and limitations

| Area | Behavior |
| --- | --- |
| Video PiP | AVPictureInPictureController receives decoded CVPixelBuffer frames through AVSampleBufferDisplayLayer. No window/screen capture. |
| Frame ownership | One waiting frame. Replaced frames are released; a frame is retained before Java frees its original reference. |
| Background playback | The native Metal/ANGLE onscreen display loop pauses while PiP can keep decoding/audio alive. |
| Pause | Native picture/audio pause without Android Activity.onPause. Repeated Play/Pause requests for the current state are ignored. |
| Resume | Recreates the player from its captured launch intent, avoiding continuation of stale live buffers. This does not guarantee refreshing tokens embedded in that intent. |
| Cold start | Requires an attached source, submitted frames and display readiness. Limited retry of the observed PG -1003 error: at most four attempts within 15 seconds. One controller remains alive for the layer's lifetime. |
| Controls | Icon only, 44-point touch area, moved 32 points left. Three-second auto-hide and tap-to-show. Pressing resets the timer; screen taps do not cancel or delay player touches. |
| Fullscreen | Android orientation requests reach iOS and update the Android viewport/resources. Menus are not globally forced into landscape. |
| Resolution changes | Queued output carries its own dimensions/format, preventing small-picture regressions during a quality change. |
| Reopening apps | Correctly parses escaped spaces in preference keys, addressing the observed second-launch numeric parse failure. |
| APK verification | Synthetic maps include the existing real APK mapping. APK bytes and signature validation remain intact. |
| Launcher | A fullscreen Web Clip routes through LiveContainer and passes Husk the chosen import's URL. Uses the icon in the user's own profile. |

## Optional CRICFy preference filter

With `.husk-hide-cricfy-banner` in that import's `java-data`, reads from `rtstv.xml` are adjusted:

- `ass`: Base64 JSON fields `sponsor.enable` and `sponsors[4].enabled` are returned as false, hiding the known fallback/banner placement.
- `message`: only the decoded notice beginning “Please update your app CRICFy v7.3” with a version boundary is returned as absent. Future-version messages, unrelated messages and malformed input pass through.

Saved originals remain unchanged. Read-time filtering survives refresh/reopen while opted in. Removing the marker restores original reads. Other ad placements and settings are preserved.

## Known limitations

- CRICFy paused PiP can still close after roughly a minute in the background. This is unresolved.
- PLAYFy resumed after a one-minute pause on the test phone; this is not a guarantee across every stream/device.
- Only Husk's native MediaCodec video path is covered. WebViews, external players, DRM and unsupported codecs can differ.
- Decoder/network compatibility otherwise remains that of Husk. This release does not make every stream URL work.
- A channel selected only in app-internal state can be lost on reconnect if the launch intent was not updated.
- The launcher inherits the guest's JIT needs. Close another running Husk guest first; Husk cannot load a second engine in one run.
- Native offsets target the exact pinned Husk 3.1 binary. Do not apply them to another version.
