import argparse,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--apple-sdk',type=Path,required=True);ap.add_argument('--llvm',type=Path,default=Path('C:/Program Files/LLVM/bin'));ap.add_argument('--base-ipa',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
def run(*x):subprocess.run([str(v) for v in x],check=True)
run(a.llvm/'clang.exe','-target','arm64-apple-ios15.0','-isysroot',a.apple_sdk,'-fobjc-arc','-fblocks','-O2','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-c',p/'HuskVideoPiP.m','-o',p/'HuskVideoPiP.o')
run(a.llvm/'clang.exe','-target','arm64-apple-ios15.0','-isysroot',a.apple_sdk,'-fobjc-arc','-fblocks','-O2','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-c',p/'HuskAppClip.m','-o',p/'HuskAppClip.o')
frameworks=['Foundation','UIKit','AVKit','AVFoundation','CoreMedia','CoreVideo','QuartzCore','AudioToolbox'];flags=[]
for f in frameworks:flags.extend(['-framework',f])
run(a.llvm/'ld64.lld.exe','-dylib','-arch','arm64','-platform_version','ios','15.0','27.1','-syslibroot',a.apple_sdk,'-install_name','@loader_path/Frameworks/HuskVideoPiP.dylib',*flags,'-lobjc','-lSystem','-adhoc_codesign',p/'HuskVideoPiP.o',p/'HuskAppClip.o','-o',p/'HuskVideoPiP.dylib')
run(a.llvm/'clang.exe','--target=aarch64-none-elf','-O2','-ffreestanding','-fno-builtin','-ffixed-x18','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Werror','-c',p/'pip_bridge.c','-o',p/'pip_bridge.o')
run(a.llvm/'clang.exe','--target=aarch64-none-elf','-c',p/'pip_trampoline.S','-o',p/'pip_trampoline.o')
run(a.llvm/'ld.lld.exe','-T',p/'pip_patch.ld',p/'pip_bridge.o',p/'pip_trampoline.o','-o',p/'pip_bridge.elf')
run(a.llvm/'llvm-objcopy.exe','-O','binary',p/'pip_bridge.elf',p/'pip_bridge.bin')
run(sys.executable,p/'package.py','--base-ipa',a.base_ipa,'--output',a.output,'--llvm',a.llvm)
