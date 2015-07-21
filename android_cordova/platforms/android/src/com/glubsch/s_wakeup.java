package com.glubsch;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;

/**
 * Created by windkol on 18.05.2015.
 */
public class s_wakeup {
    private Context mContext;
    private AlarmManager mAlarmManager=null;
    public static final String ACTION_PING = "illumino.ACTION_PING";
    public static final String ACTION_CONNECT = "illumino.ACTION_CONNECT";
    public static final String ACTION_CHECK_PING = "illumino.ACTION_CHECK_PING";
    public static final String ACTION_SHUT_DOWN = "illumino.ACTION_SHUT_DOWN";
    private s_debug mDebug = null;

    public s_wakeup(Context ServiceContext, AlarmManager systemService, s_debug serviceDebug) {
        mContext=ServiceContext;
        mAlarmManager=systemService;
        mDebug = serviceDebug;
    }

    public static Intent startIntent(Context context){
        Intent i = new Intent(context, bg_service.class);
        i.setAction(ACTION_CONNECT);
        return i;
    }

    public Runnable delayed_reconnect=new Runnable() {
        @Override
        public void run() {
            mContext.startService(startIntent(mContext));
        }
    };

    public void start_pinging(Context ct){
        Intent i = new Intent(ct, bg_service.class);
        i.setAction(ACTION_PING);
        PendingIntent operation = PendingIntent.getService(ct, 0, i, PendingIntent.FLAG_UPDATE_CURRENT);
        mAlarmManager.setInexactRepeating(AlarmManager.RTC_WAKEUP, System.currentTimeMillis(), 300000L, operation); // 5 min
        mDebug.write_to_file("wakeup for ping scheduled for now+5min");
    }

    public void start_ping_check(Context ct){
        Intent i = new Intent(ct, bg_service.class);
        i.setAction(ACTION_CHECK_PING);
        PendingIntent operation = PendingIntent.getService(ct, 0, i, PendingIntent.FLAG_UPDATE_CURRENT);
        mAlarmManager.set(AlarmManager.RTC_WAKEUP, System.currentTimeMillis()+60000L, operation); // 5 min
        mDebug.write_to_file("wakeup for ping check in 60sec");
    }

    public boolean is_pinging(Context ct){
        Intent i = new Intent(ct, bg_service.class);
        i.setAction(ACTION_PING);
        boolean state = (PendingIntent.getService(ct, 0, i, PendingIntent.FLAG_NO_CREATE) != null);
        if(state) {
            mDebug.write_to_file("Wakeup,is_pinging: ping intent is running");
        } else {
            mDebug.write_to_file("Wakeup,is_pinging: ping intent is not running!");
        }
        return  state;
    }

    public void stop_pinging(Context ct){
        Intent i = new Intent(ct, bg_service.class);
        // stop pings
        i.setAction(ACTION_PING);
        mDebug.write_to_file("cancel all wakeups!!!");
        PendingIntent operation = PendingIntent.getService(ct, 0, i, PendingIntent.FLAG_CANCEL_CURRENT);
        mAlarmManager.cancel(operation);//important
        operation.cancel();//important

        // stop ping checks
        i.setAction(ACTION_CHECK_PING);
        operation = PendingIntent.getService(ct, 0, i, PendingIntent.FLAG_CANCEL_CURRENT);
        mAlarmManager.cancel(operation);//important
        operation.cancel();//important
    }


    // to kill us
    public static Intent closeIntent(Context context){
        Intent i = new Intent(context, bg_service.class);
        i.setAction(ACTION_SHUT_DOWN);
        return i;
    }

}
