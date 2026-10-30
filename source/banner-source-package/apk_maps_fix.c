/* SPDX-License-Identifier: GPL-2.0-or-later
 * Experimental Husk 3.1 compatibility wrapper: expose the actual, already mapped
 * main APK in synthetic /proc/self/maps. No APK bytes or validation code change.
 */
typedef unsigned long size_t;
typedef unsigned long uintptr_t;
typedef struct { int fd; const unsigned char *map; size_t size; void *entries; size_t count; } Zip;
extern size_t original_maps(char *,size_t,const char *);
extern const Zip *tl_ld_apk_at(int);
extern const char *tl_ld_main_apk(void);
extern void tl_log_line(const char *,...);
static int put(char *b,size_t cap,size_t *k,char c){if(*k+1>=cap)return 0;b[(*k)++]=c;return 1;}
static int text(char *b,size_t cap,size_t *k,const char *s){while(*s)if(!put(b,cap,k,*s++))return 0;return 1;}
static int hex(char *b,size_t cap,size_t *k,uintptr_t x){char r[16];int n=0;do{unsigned v=x&15;r[n++]=(char)(v<10?'0'+v:'a'+v-10);x>>=4;}while(x);while(n)if(!put(b,cap,k,r[--n]))return 0;return 1;}
size_t compat_maps(char *buf,size_t n,const char *dir){
 size_t used=original_maps(buf,n,dir);
 if(!buf||n<2)return used;
 const Zip *z=tl_ld_apk_at(0);const char *path=tl_ld_main_apk();
 if(!z||!z->map||!z->size||!path||!*path)return used;
 char line[1536];size_t k=0;
 uintptr_t lo=(uintptr_t)z->map,hi=(lo+z->size+16383ul)&~16383ul;
 if(!hex(line,sizeof(line),&k,lo)||!put(line,sizeof(line),&k,'-')||!hex(line,sizeof(line),&k,hi)||!text(line,sizeof(line),&k," r--p 00000000 fd:00 3900 ")||!text(line,sizeof(line),&k,path)||!put(line,sizeof(line),&k,'\n')||k>=n)return used;
 if(used>=n)used=n-1;
 if(used>n-1-k)used=n-1-k;
 for(size_t i=used;i>0;i--)buf[k+i-1]=buf[i-1];
 for(size_t i=0;i<k;i++)buf[i]=line[i];
 buf[k+used]=0;tl_log_line("compat: real main APK mapping included in /proc/self/maps");return k+used;
}
