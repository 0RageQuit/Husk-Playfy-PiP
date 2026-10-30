package android.content;

import java.io.File;
import java.nio.charset.StandardCharsets;
import org.json.JSONArray;
import org.json.JSONObject;

/** Opt-in, per-data-container banner preference override for the unchanged CRICFy 7.3 APK. */
final class HuskBannerPreferences {
    static String read(File preferences, String key, String original) {
        if (original == null || (!"ass".equals(key) && !"message".equals(key)) || !"rtstv.xml".equals(preferences.getName())) return original;
        try {
            File parent = preferences.getParentFile();
            File data = parent == null ? null : parent.getParentFile();
            if (data == null || !new File(data, ".husk-hide-cricfy-banner").isFile()) return original;
            byte[] decoded = android.util.Base64.decode(original, android.util.Base64.DEFAULT);
            if ("message".equals(key)) {
                String notice = new String(decoded, StandardCharsets.UTF_8).trim().toLowerCase(java.util.Locale.ROOT);
                String prefix = "please update your app cricfy v7.3";
                if (notice.startsWith(prefix)) {
                    int n = prefix.length();
                    if (notice.length() == n || Character.isWhitespace(notice.charAt(n)) || notice.charAt(n) == '.' || notice.charAt(n) == '*') return null;
                }
                return original;
            }
            JSONObject config = new JSONObject(new String(decoded, StandardCharsets.UTF_8));
            boolean changed = false;
            JSONObject fallback = config.optJSONObject("sponsor");
            if (fallback != null && fallback.optBoolean("enable", false)) {
                fallback.put("enable", false); changed = true;
            }
            JSONArray sponsors = config.optJSONArray("sponsors");
            JSONObject banner = sponsors == null ? null : sponsors.optJSONObject(4);
            if (banner != null && banner.optBoolean("enabled", false)) {
                banner.put("enabled", false); changed = true;
            }
            if (!changed) return original;
            return android.util.Base64.encodeToString(config.toString().getBytes(StandardCharsets.UTF_8), android.util.Base64.NO_WRAP);
        } catch (Exception ignored) {
            // Unknown or malformed configuration must retain the app's original behavior.
            return original;
        }
    }
}
