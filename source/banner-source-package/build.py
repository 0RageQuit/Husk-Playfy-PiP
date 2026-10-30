import argparse,hashlib,os,plistlib,shutil,struct,subprocess,sys,zipfile,copy,json
from pathlib import Path
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('ipa',type=Path);p.add_argument('output',type=Path)
p.add_argument('--llvm',type=Path,default=Path('C:/Program Files/LLVM/bin'))
p.add_argument('--jdk',type=Path,required=True);p.add_argument('--sdk',type=Path,required=True)
args=p.parse_args();source=args.ipa.resolve();out=args.output.resolve();temp=out.with_suffix('.ipa.partial')
work=root/'build';work.mkdir(exist_ok=True)
import macho_sign
def run(command):subprocess.run([str(x) for x in command],check=True)
for name in ['apk_maps_fix','orientation_fix']:
 run([args.llvm/'clang.exe','--target=aarch64-none-elf','-O2','-ffreestanding','-fno-builtin','-ffixed-x18','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Werror','-c',root/(name+'.c'),'-o',work/(name+'.o')])
 stem='maps' if name=='apk_maps_fix' else 'orientation'
 run([args.llvm/'clang.exe','--target=aarch64-none-elf','-c',root/(stem+'_trampoline.S'),'-o',work/(stem+'_trampoline.o')])
 run([args.llvm/'ld.lld.exe','-T',root/(stem+'_patch.ld'),work/(name+'.o'),work/(stem+'_trampoline.o'),'-o',work/(name+'.elf')])
 run([args.llvm/'llvm-objcopy.exe','-O','binary',work/(name+'.elf'),work/(name+'.bin')])
archive=root/'Husk-3.1-source.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='3ea2cccb002bee26d2c5dc7c583f91bf44127e69326f7ffd74b9310b185c561a'
with zipfile.ZipFile(archive) as z:
 for item in z.infolist():
  relative=Path(*Path(item.filename).parts[1:])
  if str(relative).replace('\\','/').startswith('src/java-framework/') and not item.is_dir():
   assert '..' not in relative.parts
   target=work/'source'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
framework=work/'source/src/java-framework'
for item in (root/'changes/src/java-framework').rglob('*.java'):
 target=framework/item.relative_to(root/'changes/src/java-framework');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(item,target)
compiled=work/'fullscreen-framework';compiled.mkdir(exist_ok=True)
for name in ['stubs','classes']:(compiled/name).mkdir(exist_ok=True)
def argfile(name,paths):
 path=compiled/name;path.write_text('\n'.join('"'+str(x).replace('\\','/')+'"' for x in paths),encoding='utf-8');return '@'+str(path)
run([args.jdk/'bin/javac.exe','-nowarn','--release','8','-encoding','UTF-8','-d',compiled/'stubs',argfile('stubs.args',list((framework/'stubs').rglob('*.java')))])
run([args.jdk/'bin/javac.exe','-nowarn','--release','8','-encoding','UTF-8','-cp',compiled/'stubs','-d',compiled/'classes',argfile('sources.args',list((framework/'src').rglob('*.java'))+list((framework/'gen-src').rglob('*.java')))])
with zipfile.ZipFile(compiled/'classes.jar','w',zipfile.ZIP_DEFLATED) as z:
 for path in sorted((compiled/'classes').rglob('*.class')):z.write(path,path.relative_to(compiled/'classes').as_posix())
run([args.jdk/'bin/java.exe','-Xmx1024m','-cp',args.sdk/'build-tools/35.0.0/lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--output',compiled,compiled/'classes.jar'])
with zipfile.ZipFile(source) as z:
 original=z.read('Payload/Husk.app/Husk');pos=32
 for _ in range(struct.unpack_from('<I',original,16)[0]):
  cmd,size=struct.unpack_from('<II',original,pos)
  if cmd==0x1d:
   off,length=struct.unpack_from('<II',original,pos+8);sb=original[off:off+length]
   for i in range(struct.unpack_from('>I',sb,8)[0]):
    slot,at=struct.unpack_from('>II',sb,12+8*i)
    if slot==5:(work/'husk-original-entitlements.plist').write_bytes(sb[at+8:at+struct.unpack_from('>I',sb,at+4)[0]])
  pos+=size

assert not out.exists(), 'Preserve an existing deliverable; choose another filename'
with zipfile.ZipFile(source) as z:
 exe='Payload/Husk.app/Husk';dex='Payload/Husk.app/java-runtime/husk-framework.dex';res='Payload/Husk.app/_CodeSignature/CodeResources';info='Payload/Husk.app/Info.plist'
 original=z.read(exe)
 assert hashlib.sha256(original).hexdigest()=='fd8e72f03d40cd4871925b66aea78fbc8f8218e9b557495f956a01f495fac56e'
 b=bytearray(original)
 for old,cave,expected,filename in [(0x9c434,0x5c4140,'ff4302d1','apk_maps_fix.bin'),(0x29018,0x5c5000,'882f00d0','orientation_fix.bin')]:
  patch=(work/filename).read_bytes()
  assert b[old:old+4]==bytes.fromhex(expected),(hex(old),b[old:old+4].hex())
  assert cave+len(patch)<=0x5c8000 and set(b[cave:cave+len(patch)])=={0}
  b[cave:cave+len(patch)]=patch
  delta=(cave-old)//4;assert -(1<<25)<=delta<(1<<25)
  struct.pack_into('<I',b,old,0x14000000|(delta&0x3ffffff))
 replacement=(work/'fullscreen-framework/classes.dex').read_bytes()
 assert replacement[:8]==z.read(dex)[:8] and replacement[:4]==b'dex\n'
 resources=plistlib.loads(z.read(res));relative='java-runtime/husk-framework.dex'
 resources['files'][relative]=hashlib.sha1(replacement).digest()
 resources['files2'][relative]['hash2']=hashlib.sha256(replacement).digest()
 resource_bytes=plistlib.dumps(resources,fmt=plistlib.FMT_XML,sort_keys=True)
 patched=work/'Husk-fullscreen-fix';patched.write_bytes(b)
 identifier=plistlib.loads(z.read(info))['CFBundleIdentifier']
 ents=plistlib.loads((work/'husk-original-entitlements.plist').read_bytes())
 macho_sign.sign(str(patched),identifier,ents);final=bytearray(patched.read_bytes())
 p=32
 for i in range(struct.unpack_from('<I',final,16)[0]):
  cmd,n=struct.unpack_from('<II',final,p)
  if cmd==0x1d:sigoff,siglen=struct.unpack_from('<II',final,p+8)
  p+=n
 for i in range(struct.unpack_from('>I',final,sigoff+8)[0]):
  slot,at=struct.unpack_from('>II',final,sigoff+12+8*i)
  if slot==0:cdpos=sigoff+at
 ho,ns,nc,limit=struct.unpack_from('>IIII',final,cdpos+16)[0],struct.unpack_from('>I',final,cdpos+24)[0],struct.unpack_from('>I',final,cdpos+28)[0],struct.unpack_from('>I',final,cdpos+32)[0]
 assert ns>=3 and final[cdpos+36]==32 and final[cdpos+37]==2
 for slot,contents in [(1,z.read(info)),(3,resource_bytes)]:
  at=cdpos+ho-slot*32;final[at:at+32]=hashlib.sha256(contents).digest()
 page=1<<final[cdpos+39]
 for i in range(nc):assert hashlib.sha256(final[i*page:min((i+1)*page,limit)]).digest()==final[cdpos+ho+i*32:cdpos+ho+(i+1)*32]
 patched.write_bytes(final)
 changed={exe:final,dex:replacement,res:resource_bytes}
 with zipfile.ZipFile(temp,'w',allowZip64=True) as dest:
  for item in z.infolist():
   if item.filename in changed:dest.writestr(copy.copy(item),changed[item.filename])
   else:
    with z.open(item) as src,dest.open(copy.copy(item),'w',force_zip64=item.file_size>=2**31) as target:shutil.copyfileobj(src,target,4*1024*1024)
 with zipfile.ZipFile(temp) as dest:
  assert dest.testzip() is None
  actual=[]
  for item in z.infolist():
   if z.getinfo(item.filename).CRC!=dest.getinfo(item.filename).CRC:actual.append(item.filename)
  assert set(actual)==set(changed),actual
 temp.rename(out)
 result={'output':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'modified_entries':actual,'code_pages_verified':nc,'resource_manifest_updated':True,'info_and_resource_signature_slots_verified':True,'phone_tested':False}
 (work/'banner-package-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
