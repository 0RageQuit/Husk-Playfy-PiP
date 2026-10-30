# Add a Home Screen App Clip

The **v0.2.0 test build** adapts Husk's existing **Generate App Clip** button for LiveContainer. It generates the shortcut using your current app/import IDs, so no separate website, Python tool or somebody else's profile is needed.

This is a Home Screen Web Clip that launches your existing app through LiveContainer and Husk. It is not an Apple App Store App Clip or an independent native PLAYFy app.

## Add PLAYFy to the Home Screen

1. Install the [v0.2.0 test IPA](https://github.com/0RageQuit/Husk-Video-PiP/releases/tag/v0.2.0) in LiveContainer, keeping your Husk data. Enable JIT as usual.
2. In **Husk's library**, open the **Husk settings for your PLAYFy entry**. This is not PLAYFy's own Android settings menu.
3. Under **Home Screen**, tap **Generate App Clip**.
4. Allow the profile download. Open **Settings → Profile Downloaded → Install** and follow iOS's prompts.
5. Tap the new PLAYFy icon on the Home Screen. It routes **LiveContainer → Husk → your PLAYFy import**.

The app's name/icon and your current destination are included automatically. The generated profile uses fullscreen Web Clip mode, which avoids the earlier default-browser/Brave issue.

## If an old shortcut stopped working

Reimporting PLAYFy changes its import ID. Remove the old PLAYFy shortcut/profile and generate a new one from the current entry. Replacing Husk should keep the same data container; deleting it or changing containers may also require regenerating shortcuts.

Close another running Husk guest before launching PLAYFy this way. Existing JIT requirements still apply, and the icon does not use another sideloaded app slot.

## What changed

Only Husk's own `app.husk.clip.*` profiles containing its expected `husk://open_app` link are adapted. When Husk is hosted in LiveContainer, the original app link is wrapped in LiveContainer's launch URL with the current guest/data-container selection, and `FullScreen` is enabled. Name, icon and other profile metadata are preserved. Other property lists and standalone Husk use their original behavior.

The profile is generated locally. It contains your app/container identifiers; share it only if you intend to share that installation-specific destination. This repository does not distribute a personal profile.

**Validation:** the new module compiles, its archive/resource/code-page checks pass, and the pinned Husk profile-serialization call site is confirmed. Generating and launching a profile through the button still needs an iPhone test. v0.1.0 remains the previously user-confirmed PiP build.
