# Troubleshooting

**PLAYFy cannot connect to its servers:** for the tested v1.7 setup, rename the original APK to **`com.playfy.tv.apk` before importing it into Husk**. This is the filename confirmed in the working launch logs; the original download name was not the working import name. Renaming the file does not change its bytes or signature.

**No PiP icon:** confirm the release is installed and actual video is playing through a native player. Tap the screen to reveal the icon. WebView-only players may not be covered.

**Repeated startup taps:** tap once and wait up to 15 seconds for the readiness/startup sequence. It restores the normal player on timeout. Capture the log if it fails rather than reinstalling your APK.

**Crash on PiP:** use the release IPA, not the superseded experimental `First-Start.ipa`. That experiment replaced the controller during startup/retry and produced an AVKit crash on the test phone. The release keeps one controller alive. If it still crashes, restore your previous IPA while keeping data and report the crash log.

**CRICFy disappears while paused:** this remains a known issue. PLAYFy was more stable in the user's test. Windows frame tests do not prove paused iOS window lifetime.

**Banner/notice remains:** the opt-in marker must be in the correct import's `java-data` directory. Only the known CRICFy 7.3 schema and exact obsolete notice are filtered; other messages/placements are preserved.

When opening an issue, include release version, model, iOS/LiveContainer/APK versions, steps and whether ordinary playback still works. Redact URLs, tokens, account data and other private information before posting logs publicly.

