import android.content.*;import java.io.*;import java.nio.charset.*;
public class UpdateNoticeTest {
 static void check(boolean v,String s){if(!v)throw new AssertionError(s);}
 static String enc(String s){return android.util.Base64.encodeToString(s.getBytes(StandardCharsets.UTF_8),2);}
 public static void main(String[] args)throws Exception{
 File root=new File(args[0]),dir=new File(root,"shared_prefs");dir.mkdirs();File flag=new File(root,".husk-hide-cricfy-banner");flag.delete();
 HuskSharedPreferences p=new HuskSharedPreferences(new File(dir,"rtstv.xml"));
 String notice=enc("Please update your app CRICFy v7.3 ... Tap here to update now ...*https://example.invalid");
 p.edit().putString("message",notice).commit();check(notice.equals(p.getString("message",null)),"opt-out pass-through");flag.createNewFile();check(p.getString("message",null)==null,"known notice absent");check(notice.equals(p.getAll().get("message")),"saved original retained");
 p.edit().putString("message",notice).commit();check(new HuskSharedPreferences(new File(dir,"rtstv.xml")).getString("message",null)==null,"refresh/reopen stays hidden");
 for(String other:new String[]{enc("Please update your app CRICFy v7.4 ..."),enc("Please update your app CRICFy v7.30 ..."),enc("Important service notice"),"not-valid-base64"}){p.edit().putString("message",other).commit();check(other.equals(p.getString("message",null)),"unrelated/future/malformed preserved");}
 p.edit().putString("other",notice).commit();check(notice.equals(p.getString("other",null)),"other key retained");
 HuskSharedPreferences other=new HuskSharedPreferences(new File(dir,"other.xml"));other.edit().putString("message",notice).commit();check(notice.equals(other.getString("message",null)),"other file retained");
 p.edit().putString("message",notice).commit();flag.delete();check(notice.equals(p.getString("message",null)),"flag removal restores exact notice");
 System.out.println("PASS: exact current-version notice hidden; opt-in, stored original, future messages, malformed input, refresh/reopen and restoration verified");
 }
}
