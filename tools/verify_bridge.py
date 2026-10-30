"""Execute candidate ARM64 hooks at two slides. Apple PiP APIs are NOT modeled here."""
import sys,struct,json,subprocess,argparse
from pathlib import Path
from unicorn import *
from unicorn.arm64_const import *
parser=argparse.ArgumentParser();parser.add_argument('--original-executable',type=Path,required=True);parser.add_argument('--llvm',type=Path,default=Path('C:/Program Files/LLVM/bin'));cli=parser.parse_args()
p=Path(__file__).resolve().parents[1]/'source/pip'
symbols={}
for line in subprocess.check_output([str(cli.llvm/'llvm-nm.exe'),'-n',str(p/'pip_bridge.elf')],text=True).splitlines():
 a,t,n=line.split();symbols[n]=int(a,16)
original=cli.original_executable.read_bytes();patch=(p/'pip_bridge.bin').read_bytes();cases=0
for slide in [0,0x234000000]:
 b=0x100000000+slide;u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(b,0xa00000);u.mem_write(b,original[:0x5c8000]);u.mem_write(b+0x5c5400,patch)
 u.mem_write(b+0x613a50,struct.pack('<Q',0xcafebabe))
 arena=0x800000000;u.mem_map(arena,0x30000);stop=arena;sp=arena+0x28000;args=arena+0x1000;ret=arena+0x2000;frame=arena+0x3000;enqueue=arena+0x4000;policy=arena+0x5000
 for old,name in [(0x4b7cc,'pip_render'),(0xbc280,'pip_pause')]:u.mem_write(b+old,struct.pack('<I',0x14000000|(((symbols[name]+slide-(b+old))//4)&0x3ffffff)))
 state={};events=[]
 def returns():u.reg_write(UC_ARM64_REG_PC,u.reg_read(UC_ARM64_REG_LR))
 def hook(uc,a,size,data):
  if a==b+0x4b7d0:
   # Check replayed original stack allocation; restore it as the original epilogue would.
   uc.reg_write(UC_ARM64_REG_SP,uc.reg_read(UC_ARM64_REG_SP)+0xc0)
   uc.mem_write(ret,bytes([state['render_ok']])+b'\0'*7);uc.reg_write(UC_ARM64_REG_W0,state['native_ok']);events.append('render');returns()
  elif a==b+0xbc284:
   assert uc.reg_read(UC_ARM64_REG_X8)==b+0x872000
   events.append(('original_pause',uc.reg_read(UC_ARM64_REG_W0)));returns()
  elif a==b+0x46a3b8:
   assert uc.reg_read(UC_ARM64_REG_X0)==0xfffffffffffffffe
   at=uc.reg_read(UC_ARM64_REG_X1);name=bytes(uc.mem_read(at,80)).split(b'\0')[0]
   result=enqueue if name==b'husk_video_pip_enqueue' else policy
   uc.reg_write(UC_ARM64_REG_X0,result if state['loaded'] else 0);returns()
  elif a==enqueue:
   assert uc.reg_read(UC_ARM64_REG_X0)==0xdeadbeef
   assert uc.reg_read(UC_ARM64_REG_X1)==12345678
   assert uc.reg_read(UC_ARM64_REG_X3)==0xcafebabe
   assert uc.reg_read(UC_ARM64_REG_X2)==symbols['pip_playback_control']+slide
   events.append('enqueue');returns()
  elif a==policy:
   events.append(('policy',uc.reg_read(UC_ARM64_REG_W0)));uc.reg_write(UC_ARM64_REG_W0,state['mode']);returns()
  elif a==b+0x60d0:events.append(('audio',uc.reg_read(UC_ARM64_REG_W0)));returns()
  elif a==b+0x2603c:
   phase=uc.reg_read(UC_ARM64_REG_W0);assert phase in [6,10]
   events.append(('lifecycle' if phase==6 else 'reconnect',uc.reg_read(UC_ARM64_REG_W1)));returns()
  elif a==stop:uc.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook)
 saved=[UC_ARM64_REG_X18,UC_ARM64_REG_X19,UC_ARM64_REG_X20,UC_ARM64_REG_X21,UC_ARM64_REG_X22,UC_ARM64_REG_X23,UC_ARM64_REG_X24,UC_ARM64_REG_X25,UC_ARM64_REG_X26,UC_ARM64_REG_X27,UC_ARM64_REG_X28,UC_ARM64_REG_X29]
 def run(addr,x0,x1=0,x2=0):
  global cases
  events.clear()
  for i,r in enumerate(saved):u.reg_write(r,0xabc000+i)
  u.reg_write(UC_ARM64_REG_SP,sp);u.reg_write(UC_ARM64_REG_LR,stop)
  for r,v in [(UC_ARM64_REG_X0,x0),(UC_ARM64_REG_X1,x1),(UC_ARM64_REG_X2,x2)]:u.reg_write(r,v)
  u.emu_start(addr,stop+4,count=10000)
  assert u.reg_read(UC_ARM64_REG_SP)==sp
  for i,r in enumerate(saved):assert u.reg_read(r)==0xabc000+i
  cases+=1
 for loaded in [False,True]:
  for native_ok in [0,1]:
   for render_ok in [0,1]:
    for frame_valid in [False,True]:
     for pixel_valid in [False,True]:
      state.update(loaded=loaded,native_ok=native_ok,render_ok=render_ok)
      u.mem_write(args,struct.pack('<Q',frame if frame_valid else 0));u.mem_write(frame,struct.pack('<QQQ',0xdeadbeef if pixel_valid else 0,12345678,0))
      run(b+0x4b7cc,0,args,ret)
      assert ('enqueue' in events)==bool(loaded and native_ok and render_ok and frame_valid and pixel_valid)
      assert u.reg_read(UC_ARM64_REG_W0)==native_ok
 for loaded in [False,True]:
  for mode in range(8):
   for background in [0,1]:
    state.update(loaded=loaded,mode=mode);u.mem_write(b+0x620cd1,b'\0')
    run(b+0xbc280,background)
    if loaded and mode&1:
     assert bytes(u.mem_read(b+0x620cd1,1))==bytes([int(bool(background or ((mode&2) and not(mode&4))))])
     assert not any(isinstance(x,tuple) and x[0]=='original_pause' for x in events)
     assert (('audio',1) in events)==bool((mode&2) and not(mode&4))
    else:assert ('original_pause',background) in events
 for background in [0,1]:
  for playing in [0,1,2,3,4]:
   run(symbols['pip_playback_control']+slide,background,playing)
   if playing==4:
    assert bytes(u.mem_read(b+0x620cd1,1))==b'\x01'
    assert events==[('audio',1)], 'PiP pause must not send Android lifecycle events'
    continue
   assert bytes(u.mem_read(b+0x620cd1,1))==bytes([int(background or not playing)])
   assert events==[('audio',int(not playing)),('lifecycle',int(not playing))]+([('reconnect',1)] if playing==3 else [])
result={'actual_arm64_cases_passed':cases,'aslr_slides':2,'callee_saved_registers_preserved':True,'phone_tested':False,'native_pip_tested':False}
(Path(__file__).resolve().parents[1]/'_build/bridge-test-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
