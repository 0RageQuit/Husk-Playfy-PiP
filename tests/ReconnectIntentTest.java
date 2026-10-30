import android.content.Intent;
import android.content.ComponentName;
public final class ReconnectIntentTest {
 public static void main(String[] args) {
  Intent old = new Intent("android.intent.action.VIEW");
  old.setComponent(new ComponentName("com.example.player", "com.example.player.Live"));
  old.putExtra("stream", "https://example.invalid/live.m3u8");
  old.putExtra("channelIndex", 7);
  old.addFlags(0x10000000);
  Intent selected = new Intent(old);
  // A releasing player may clear or alter its own original intent during destruction.
  old.removeExtra("stream"); old.putExtra("channelIndex", 0); old.setComponent(null);
  if (!"https://example.invalid/live.m3u8".equals(selected.getStringExtra("stream"))) throw new AssertionError("selection lost");
  if (selected.getIntExtra("channelIndex", -1) != 7) throw new AssertionError("channel lost");
  if (!"com.example.player.Live".equals(selected.getComponent().getClassName())) throw new AssertionError("component lost");
  if (selected.getFlags() != 0x10000000) throw new AssertionError("flags lost");
  System.out.println("PASS: actual Husk Intent retains stream, channel, component and flags after original teardown mutations");
 }
}
