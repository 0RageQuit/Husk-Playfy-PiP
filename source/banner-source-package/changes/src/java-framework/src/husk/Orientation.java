package husk;

import android.app.Activity;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.os.Handler;
import android.os.Looper;

/** Connect an activity's orientation request to host rotation and Android's configuration lifecycle. */
public final class Orientation {
    private static int launchOrientation;
    private static int lastWidth, lastHeight;
    private static boolean pending;
    private Orientation() {}

    public static void request(int requested) {
        if (launchOrientation == 0) {
            lastWidth = Native.screenWidth(); lastHeight = Native.screenHeight();
            launchOrientation = lastWidth > lastHeight ? 6 : 1;
        }
        // An unspecified activity returns to the launch aspect instead of inheriting a player it covered.
        Native.setOrientation(requested == -1 ? launchOrientation : requested);
        if (!pending) {
            pending = true;
            new Handler(Looper.getMainLooper()).post(Orientation::applyConfiguration);
        }
    }

    private static void applyConfiguration() {
        pending = false;
        int width = Native.screenWidth(), height = Native.screenHeight();
        if (width == lastWidth && height == lastHeight) return;
        lastWidth = width; lastHeight = height;
        Resources.huskScreenChanged(width, height);
        Activity activity = AppRunner.top();
        if (activity != null && !activity.isFinishing()) {
            Configuration config = new Configuration(activity.getResources().getConfiguration());
            activity.getApplication().onConfigurationChanged(config);
            activity.onConfigurationChanged(config);
        }
        ViewRoot.screenChanged();
    }
}
