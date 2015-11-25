package com.glubsch;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.support.v4.app.NotificationCompat;
import android.util.Log;

import org.apache.cordova.plugin.GetLogin;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

/**
 * Created by windkol on 18.05.2015.
 */
public class s_notify {

    private NotificationCompat.Builder mNotificationBuilder = null;
    private NotificationManager mNotificationManager = null;
    private Context mContext;
    public Bitmap last_picture = null;
    private SharedPreferences mSettings;
    private String area_of_last_alert = "";
    private String time_of_last_alert = "";
    private String mVersion = "1.42";
    private String lastTitle="";
    private String lastAreaText="";

    public s_notify(Context serviceContext, SharedPreferences serviceSettings) {
        mContext = serviceContext;
        mNotificationBuilder = new NotificationCompat.Builder(mContext);
        mSettings = serviceSettings;
    }

    public void set_area(String area){
        area_of_last_alert=area;
    }

    public void set_time(){
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm");
        time_of_last_alert=sdf.format(new Date());
    }

    public void set_image(Bitmap pic){
        last_picture=pic;
    }

    public void setupNotifications(NotificationManager systemService) { //called in onCreate()
        if (mNotificationManager == null) {
            mNotificationManager = systemService;
        }
        PendingIntent pendingIntent = PendingIntent.getActivity(mContext, 0, new Intent(mContext, MainActivity.class).setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP), 0);
        //PendingIntent pendingCloseIntent = PendingIntent.getActivity(this, 0,new Intent(this, MainActivity.class).setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP),0);
        mNotificationBuilder
                .setSmallIcon(R.drawable.logobw)
                //.setCategory(NotificationCompat.CATEGORY_SERVICE)
                //.setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setContentTitle("")
                .setWhen(System.currentTimeMillis())
                .setContentIntent(pendingIntent)
                //.addAction(android.R.drawable.ic_menu_close_clear_cancel,"exit", pendingCloseIntent)
                .setOngoing(true);
    }


    public void showNotification(String title, String short_text, String long_text) {
        if (last_picture == null) {
            String login = mSettings.getString("LOGIN", MainActivity.nongoodlogin);
            String shown_title = login + " @ "+mContext.getString(R.string.app_name)+" " + mVersion;

            // avoid showing old-pre-logout status
            if(login.equals(MainActivity.nongoodlogin)){
                shown_title=mContext.getString(R.string.app_name);
                short_text="Log-in to activate your protection";
                long_text=short_text;
            }

            mNotificationBuilder
                    .setContentTitle(shown_title)
                    .setWhen(System.currentTimeMillis())
                            //.setContentInfo("shor first line, right")
                    .setContentText(short_text)
                    .setStyle(new NotificationCompat.BigTextStyle().bigText(long_text)); //.setSummaryText(short_text+"3"));this will be shown if you pull down the menu
            displayNotification();
        } else {
            String Message = "Alert at " + area_of_last_alert + " " + time_of_last_alert + "! " + short_text + ".";
            showNotification(title, Message, last_picture);
        }
    }

    public void showNotification(String title, String short_text, Bitmap picture) {
        lastTitle=title;
        mNotificationBuilder
                .setAutoCancel(true)
                //.setVibrate(new long[]{1000, 1000, 1000, 1000, 1000, 1000})
                //.setPriority(Notification.PRIORITY_HIGH)
                .setContentTitle(title)
                .setContentText(short_text)
                .setStyle(new NotificationCompat.BigPictureStyle().bigPicture(picture).setSummaryText(short_text));
        displayNotification();
    }

    public void displayNotification() {
        if (mNotificationManager != null) {
            mNotificationManager.notify(1, mNotificationBuilder.build());
        }
    }

    public String Notification_text_builder(boolean l_t, ArrayList<s_area> areas) {
        String not = "";
        String p= "Protected";
        String m= "Movement";
        if (l_t) {
            for (int i = 0; i < areas.size(); i++) {
                not += areas.get(i).getName() + ": ";

                if(areas.get(i).getAlarmSum()>0){
                not += String.valueOf(areas.get(i).getAlarmSum())+ " Alarms! ";
                    p="P.";
                    m="M.";
                }

                if (areas.get(i).getDetection() >= 1) {
                    not += " "+p;
                } else {
                    not += "NOT "+p;
                }

                if (areas.get(i).getState() >= 1) {
                    not += " / "+m;
                } else {
                    not += " / No "+m;
                }
                not += "\n";
            }

            //not += ((bg_service)mContext).getDistanceDebug(); // add distance debug info
        } else {
            int detection_on = 0;
            int alarms = 0;
            //Log.i(getString(R.string.debug_id),"we have "+String.valueOf(areas.size())+" areas");
            for (int i = 0; i < areas.size(); i++) {
                if (areas.get(i).getDetection() >= 1) {
                    detection_on++;
                }
                alarms+=areas.get(i).getAlarmSum();
            }
            if(alarms>0){
                not += String.valueOf(alarms) + " Alarm";
                if(alarms>1){
                    not+="s";
                }
                not +="! ";
            }
            not += String.valueOf(detection_on) + "/" + String.valueOf(areas.size()) + " Areas protected";
            lastAreaText=not;
        }

        return not;
    }


    public void clear_image() {
        //Log.e(mContext.getString(R.string.debug_id), "CLEARING IMAGE");
        set_image(null);
    }

    /*
    public void restore(){
        Log.e(mContext.getString(R.string.debug_id), "RESTORE it to "+lastTitle+" and "+lastAreaText);
        showNotification(lastTitle, lastAreaText,"");
    }
    */
}
