import argparse
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--original-ipa', type=Path, required=True)
p.add_argument('--ios-sdk', type=Path, required=True)
p.add_argument('--jdk', type=Path, required=True)
p.add_argument('--android-sdk', type=Path, required=True)
p.add_argument('--llvm', type=Path, default=Path('C:/Program Files/LLVM/bin'))
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
work = root / '_build'
work.mkdir(exist_ok=True)
base = work / 'husk-java-base.ipa'
if base.exists():
    raise SystemExit('Existing base preserved. Move _build/husk-java-base.ipa aside for a fresh build.')

def run(*args):
    subprocess.run([str(v) for v in args], check=True)

run(sys.executable, root/'source/banner-source-package/build.py',
    a.original_ipa.resolve(), base, '--jdk', a.jdk.resolve(),
    '--sdk', a.android_sdk.resolve(), '--llvm', a.llvm.resolve())
run(sys.executable, root/'source/pip/build.py',
    '--apple-sdk', a.ios_sdk.resolve(), '--base-ipa', base,
    '--output', a.output.resolve(), '--llvm', a.llvm.resolve())
