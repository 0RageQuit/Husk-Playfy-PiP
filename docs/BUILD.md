# Build on Windows

Pinned base: Husk 3.1, commit `7cc583ce3fccd271eea9087483ddc5e49af14d8d`. The full source archive and all changes are included. APKs are not build inputs.

Tested inputs/tools:

- Original, unmodified upstream Husk 3.1 IPA.
- Python 3 and LLVM 23.1.4, including clang, ld.lld, ld64.lld, llvm-nm and llvm-objcopy.
- Temurin JDK 21.0.13+9 and Android SDK build-tools 35.0.0.
- A locally supplied iPhoneOS SDK; tested version 27.1.

From the repository root:

    python build.py --original-ipa PATH/TO/Husk-3.1-original.ipa --ios-sdk PATH/TO/iPhoneOS.sdk --jdk PATH/TO/JDK --android-sdk PATH/TO/ANDROID-SDK --llvm "C:/Program Files/LLVM/bin" --output PATH/TO/Husk-Video-PiP.ipa

Stage one extracts the pinned Java framework, overlays the source changes, compiles it, builds the mapping/orientation hooks, updates resource seals and signs offline. Stage two builds the PiP module/bridge, adds its loader-relative dependency, updates resources and signs offline. Nothing installs or signs onto a device.

The source archive SHA256 is `3ea2cccb002bee26d2c5dc7c583f91bf44127e69326f7ffd74b9310b185c561a`; original executable SHA256 is `fd8e72f03d40cd4871925b66aea78fbc8f8218e9b557495f956a01f495fac56e`.

With the tested toolchain, the current base IPA SHA256 is `2da70e1087e4e8af22b4f06e036b849aa53dffa07cfbb0bfdac7d0c512934479`. The packager accepts only known base hashes. Another compiler/JDK may differ: investigate source/binary differences before adding a new accepted hash. Do not remove exact-build checks to patch an arbitrary version.

Source map:

- `source/banner-source-package/Husk-3.1-source.zip`: complete upstream tree.
- `source/banner-source-package/changes`: modified Java classes.
- Base `*.c`, `*.S`, `*.ld`: APK mapping/orientation hooks.
- `source/pip/HuskVideoPiP.m`: native PiP, UI, readiness and transport controls.
- `source/pip/HuskAppClip.m`: targeted adapter for Husk's generated App Clip profiles when hosted in LiveContainer.
- `source/pip/frame_mailbox.h`: bounded frame handoff.
- `source/pip/pip_bridge.c`, `pip_trampoline.S`, `pip_patch.ld`: pinned native hooks.

SDKs, provisioning profiles and signing identities are not bundled. The output is ad-hoc signed for later import/signing by LiveContainer or the user's normal workflow.
