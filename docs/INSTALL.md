# Setup

1. [Download the Husk IPA](https://github.com/0RageQuit/Husk-Video-PiP/releases/latest) and install it in **LiveContainer**.
2. Install [StikDebug](https://github.com/StikDebug/StikDebug/releases/latest), import your device's [pairing file](https://github.com/StikDebug/StikDebug-Guide/blob/main/pairing_file.md), and enable **LocalDevVPN** as described in [StikDebug's setup guide](https://github.com/StikDebug/StikDebug#how-to-enable-jit).
3. In **LiveContainer → Settings → JIT**, select **StikDebug** as the JIT enabler.
4. In LiveContainer, **hold Husk → Settings**, enable **Launch with JIT**, then use **JIT Launch Script** to select **`universal.js`**. [Download LiveContainer's universal.js](https://raw.githubusercontent.com/LiveContainer/LiveContainer/main/Resources/universal.js) to Files first if needed. This is the setting for **Husk inside LiveContainer**, not PLAYFy's Android settings. On the tested iOS 27 setup, selecting this script is required; enabling JIT alone is not enough.
5. Launch Husk from LiveContainer and let StikDebug complete the JIT attachment. Keep LocalDevVPN connected during this process.
6. [Download PLAYFy APK](https://playfy.net/#dl), rename the file to **`com.playfy.tv.apk`**, then import it into Husk.
7. Open PLAYFy, play a stream and tap the **PiP icon** to watch while using other apps.

Tap the screen to reveal the PiP icon if it is hidden. PLAYFy v1.7 is the tested APK version.

For a Home Screen icon, use the [built-in Generate App Clip guide](APP_CLIPS.md) with the v0.2.0 test build.

## StikDebug inside LiveContainer

If StikDebug is itself installed in LiveContainer, configure its pairing file, convert it to a **shared app**, and select **StikDebug (Another LiveContainer/Multitask)** instead. Keep another LiveContainer instance available for it. Husk still needs **Launch with JIT** and **`universal.js`** selected. See [LiveContainer’s JIT guide](https://livecontainer.github.io/docs/guides/jit-support).

## Optional CRICFy filters

Create an empty file named `.husk-hide-cricfy-banner` in the CRICFy import's `java-data` directory using your usual app-document file access. Inside the Husk data container the relative location is:

    Documents/TranslationLayer/<CRICFY-IMPORT-ID>/java-data/.husk-hide-cricfy-banner

The enclosing LiveContainer container UUID is specific to your phone. The filters are described in [Features](FEATURES.md). They do not rewrite the APK or stored preferences. Remove the marker and reopen the app to restore original reads. This is not an all-app ad blocker.
