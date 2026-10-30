# Verification

The latest release IPA was reported working on an iPhone 16 Plus running iOS 27.0.1 in LiveContainer. Playback, fullscreen, resolution changes, background recovery and channel switching were reported working. PLAYFy resumed after a one-minute pause. CRICFy's paused-window closure remains unresolved.

The public source tree was rebuilt from scratch with the documented toolchain. Its output matched the user-confirmed working IPA byte for byte (SHA256 in `BUILD-MANIFEST.json`).

PC checks:

- iOS ARM64 module compiles with warnings treated as errors.
- 148 cases execute the actual native bridge under Unicorn at two relocation slides, preserving stack/callee-saved registers. PiP transport pause is checked not to send an Android lifecycle pause.
- Actual Husk Intent snapshot test retains stream/channel/component/flags after changes to the original.
- Preference tests cover opt-in/out, saved originals, refresh/reopen, malformed/unrelated/future-version messages, marker removal and earlier banner behavior.
- Release preference-helper class matches tested class bytes.
- 4,227 main executable and 25 PiP dylib code-signature pages, resource seal and archive verified.
- Previous tested MediaCodec class retained.

A separate continuous Windows test exercises production `frame_mailbox.h` with modeled frame references and a Windows mutex backend. It does not run AVKit, CoreVideo, VideoToolbox, native audio or actual phone playback. It was still running during initial release preparation; no completed four-hour result is claimed here. Any final result must distinguish measured runtime and interruptions from the authorized work window.

Java host tests are in `tests/`; their Handler/Looper/Log stubs do not emulate Android UI or iOS frameworks.

After building, the actual native bridge harness can be run with the original extracted Husk executable:

    python -m pip install unicorn
    python tools/verify_bridge.py --original-executable PATH/TO/ORIGINAL/Husk --llvm "C:/Program Files/LLVM/bin"
