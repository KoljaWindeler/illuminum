package com.example.kolja.Illumino;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Created by kolja on 5/16/15.
 */
public class s_autostart extends BroadcastReceiver
{
    public void onReceive(Context arg0, Intent arg1)
    {
        Intent intent = new Intent(arg0,bg_service.class);
        arg0.startService(intent);
        Log.i("Autostart", "started");
    }
}
