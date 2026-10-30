# Install and use

## Replace Husk

1. Keep a copy of your working IPA. Download this project's IPA from Releases.
2. Import it in LiveContainer and replace the existing Husk entry. **Keep the current data container. Do not delete Husk first.**
3. Fully close the old Husk guest before opening the replacement.
4. Keep your existing JIT/sideloading setup. This project does not activate JIT or change app limits.
5. Open your existing PLAYFy/CRICFy import, or import your own original APK.

For the tested CRICFy 7.3 path, retain the original APK bytes and use `com.cricfytv.sports.apk` as the import filename. Its native verification expects the package name in the mapped APK path. Renaming the file does not change its bytes. Do not patch or re-sign the APK for this build.

## Use PiP

1. Start a video.
2. Tap the small PiP icon near the upper right. It is slightly left of the corner to avoid the app's controls.
3. A temporary video-only panel appears. Wait up to 15 seconds. The observed transient startup error gets at most four attempts within that request.
4. Once PiP opens, swipe Home or switch apps.

The icon appears for three seconds after video begins or you tap the screen. It stays visible while pressed. Use this video icon, rather than LiveContainer's whole-window PiP control.

Pause stops picture/audio without posting an Android activity-pause event. Play requests a fresh player from its captured launch selection; a short reconnect delay is expected. If the app changes channel internally without updating its launch intent, reconnect can return to the original selection.

Closing PiP in the background restores normal host pause behavior. Returning to Husk restores the ordinary player interface and its requested orientation.

**Known issue:** CRICFy's paused PiP can close after about a minute backgrounded. PLAYFy was reported to handle the same interval better.

## Home Screen launcher

Follow [the shortcut guide](../shortcuts/README.md). Use your own two generated profiles; another phone's IDs will not reliably target your import. Close a different running Husk guest before launching PLAYFy this way.

## Optional CRICFy filters

Create an empty file named `.husk-hide-cricfy-banner` in the CRICFy import's `java-data` directory using your usual app-document file access. Inside the Husk data container the relative location is:

    Documents/TranslationLayer/<CRICFY-IMPORT-ID>/java-data/.husk-hide-cricfy-banner

The enclosing LiveContainer container UUID is specific to your phone. The filters are described in [Features](FEATURES.md). They do not rewrite the APK or stored preferences. Remove the marker and reopen the app to restore original reads. This is not an all-app ad blocker.
