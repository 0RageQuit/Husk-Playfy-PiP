import copy,hashlib,json,plistlib,struct,sys,zipfile,shutil,argparse
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'banner-source-package'))
import macho_sign
parser=argparse.ArgumentParser();parser.add_argument('--llvm',type=Path,default=Path('C:/Program Files/LLVM/bin'));parser.add_argument('--base-ipa',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
source=args.base_ipa.resolve();out=args.output.resolve()
exe='Payload/Husk.app/Husk';res='Payload/Husk.app/_CodeSignature/CodeResources';info='Payload/Husk.app/Info.plist';lib='Payload/Husk.app/Frameworks/HuskVideoPiP.dylib'
assert hashlib.sha256(source.read_bytes()).hexdigest() in {'450a5ff9ffe57b62571d8db450b2918b93cdce2c38ff814ca1c1ac6db1a1eb3f','5403bd03a556fdd1393bc7ccb452d5bf919fdafee56ae6f1ceff02f2b25b75e4','2da70e1087e4e8af22b4f06e036b849aa53dffa07cfbb0bfdac7d0c512934479'}
# Read ELF symbols from its build map, not hand-maintained offsets.
import subprocess
symbols={}
for line in subprocess.check_output([str(args.llvm/'llvm-nm.exe'),'-n',str(root/'pip_bridge.elf')],text=True).splitlines():
 a,t,n=line.split();symbols[n]=int(a,16)
with zipfile.ZipFile(source) as z:
 b=bytearray(z.read(exe));patch=(root/'pip_bridge.bin').read_bytes();cave=0x5c5400
 assert len(patch)<0x2c00 and not any(b[cave:cave+len(patch)])
 b[cave:cave+len(patch)]=patch
 for old,name,expected in [(0x4b7cc,'pip_render','ff0303d1'),(0xbc280,'pip_pause','a83d00d0')]:
  assert b[old:old+4]==bytes.fromhex(expected)
  delta=(symbols[name]-0x100000000-old)//4
  struct.pack_into('<I',b,old,0x14000000|(delta&0x3ffffff))
 count,size=struct.unpack_from('<II',b,16);end=32+size
 path=b'@loader_path/Frameworks/HuskVideoPiP.dylib\0';n=(24+len(path)+7)&~7
 command=struct.pack('<IIIIII',0xc,n,24,0,0,0)+path
 command+=b'\0'*(n-len(command))
 assert end+n<=0x4000 and not any(b[end:end+n]);b[end:end+n]=command
 struct.pack_into('<II',b,16,count+1,size+n)
 dylib=(root/'HuskVideoPiP.dylib').read_bytes()
 resources=plistlib.loads(z.read(res));relative='Frameworks/HuskVideoPiP.dylib'
 # A standalone dylib is a sealed file resource; LiveContainer re-signs embedded Mach-O code on import.
 resources['files'][relative]=hashlib.sha1(dylib).digest()
 resources['files2'][relative]={'hash2':hashlib.sha256(dylib).digest()}
 resource_bytes=plistlib.dumps(resources,fmt=plistlib.FMT_XML,sort_keys=True)
 output_work=root.parents[1]/'_build';output_work.mkdir(exist_ok=True);patched=output_work/'Husk-PiP';patched.write_bytes(b)
 identifier=plistlib.loads(z.read(info))['CFBundleIdentifier']
 ents=plistlib.loads((root.parent/'banner-source-package/build/husk-original-entitlements.plist').read_bytes())
 macho_sign.sign(str(patched),identifier,ents)
 final=bytearray(patched.read_bytes());p=32
 for i in range(struct.unpack_from('<I',final,16)[0]):
  cmd,n=struct.unpack_from('<II',final,p)
  if cmd==0x1d:sigoff,siglen=struct.unpack_from('<II',final,p+8)
  p+=n
 for i in range(struct.unpack_from('>I',final,sigoff+8)[0]):
  slot,at=struct.unpack_from('>II',final,sigoff+12+8*i)
  if slot==0:cdpos=sigoff+at
 ho=struct.unpack_from('>I',final,cdpos+16)[0];ns,nc,limit=struct.unpack_from('>III',final,cdpos+24)
 assert ns>=3 and final[cdpos+36:cdpos+38]==bytes([32,2])
 for slot,contents in [(1,z.read(info)),(3,resource_bytes)]:
  at=cdpos+ho-slot*32;final[at:at+32]=hashlib.sha256(contents).digest()
 page=1<<final[cdpos+39]
 for i in range(nc):assert hashlib.sha256(final[i*page:min((i+1)*page,limit)]).digest()==final[cdpos+ho+i*32:cdpos+ho+(i+1)*32]
 patched.write_bytes(final)
 changed={exe:final,res:resource_bytes}
 temp=out.with_suffix('.ipa.partial')
 with zipfile.ZipFile(temp,'w',allowZip64=True) as dest:
  for item in z.infolist():
   if item.filename in changed:dest.writestr(copy.copy(item),changed[item.filename])
   else:
    with z.open(item) as src,dest.open(copy.copy(item),'w',force_zip64=item.file_size>=2**31) as target:shutil.copyfileobj(src,target,4*1024*1024)
  item=zipfile.ZipInfo(lib);item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100755<<16
  dest.writestr(item,dylib)
 with zipfile.ZipFile(temp) as dest:
  assert dest.testzip() is None
  actual=[i.filename for i in z.infolist() if hashlib.sha256(z.read(i)).digest()!=hashlib.sha256(dest.read(i.filename)).digest()]
  assert set(actual)==set(changed)
  assert dest.read('Payload/Husk.app/java-runtime/husk-framework.dex')==z.read('Payload/Husk.app/java-runtime/husk-framework.dex')
 temp.replace(out)
 result={'ipa':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'changed_entries':actual,'added_entry':lib,'main_signature_pages':nc,'phone_tested':False,'native_pip_tested':False}
 (root.parents[1]/'_build/pip-package-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
