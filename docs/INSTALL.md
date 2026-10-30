# Setup

1. [Download the Husk IPA](https://github.com/0RageQuit/Husk-Video-PiP/releases/latest).
2. Install Husk in **LiveContainer**.
3. Enable **JIT** for LiveContainer/Husk using your preferred JIT method.
4. [Download PLAYFy APK](https://playfy.net/#dl), rename the file to **`com.playfy.tv.apk`**, then import it into Husk.
5. Open PLAYFy, play a stream and tap the **PiP icon**. You can then switch apps while watching.

Tap the screen to reveal the PiP icon if it is hidden. PLAYFy v1.7 is the tested APK version.

For a Home Screen icon, use the [built-in Generate App Clip guide](APP_CLIPS.md) with the v0.2.0 test build.

## Optional CRICFy filters

Create an empty file named `.husk-hide-cricfy-banner` in the CRICFy import's `java-data` directory using your usual app-document file access. Inside the Husk data container the relative location is:

    Documents/TranslationLayer/<CRICFY-IMPORT-ID>/java-data/.husk-hide-cricfy-banner

The enclosing LiveContainer container UUID is specific to your phone. The filters are described in [Features](FEATURES.md). They do not rewrite the APK or stored preferences. Remove the marker and reopen the app to restore original reads. This is not an all-app ad blocker.
