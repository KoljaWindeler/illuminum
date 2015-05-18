package com.example.kolja.Illumino;

import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.support.v4.app.NotificationCompat;

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
    private Bitmap last_picture = null;
    private SharedPreferences mSettings;
    private String area_of_last_alert = "";
    private String time_of_last_alert = "";

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
                .setCategory(NotificationCompat.CATEGORY_SERVICE)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setContentTitle("")
                .setWhen(System.currentTimeMillis())
                .setContentIntent(pendingIntent)
                //.addAction(android.R.drawable.ic_menu_close_clear_cancel,"exit", pendingCloseIntent)
                .setOngoing(true);
    }

    public void showNotification(String title, String short_text, String long_text) {
        if (last_picture == null) {
            String login = mSettings.getString("LOGIN", "Kolja");
            mNotificationBuilder
                    .setContentTitle(login + "@" + title)
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
        mNotificationBuilder
                .setContentTitle(title)
                .setContentText(short_text)
                .setStyle(new NotificationCompat.BigPictureStyle().bigPicture(picture).setSummaryText(short_text));
        displayNotification();
    }

    private void displayNotification() {
        if (mNotificationManager != null) {
            mNotificationManager.notify(1, mNotificationBuilder.build());
        }
    }

    public String Notification_text_builder(boolean l_t, ArrayList<s_area> areas) {
        String not = "";
        if (l_t) {
            for (int i = 0; i < areas.size(); i++) {
                not += areas.get(i).getName() + ": ";
                if(areas.get(i).getDetection() >= 1) {
                    not += "Protected";
                } else {
                    not += "NOT protected";
                }

                if (areas.get(i).getState() >= 1) {
                    not += " / Movement";
                } else {
                    not += " / No Movement";
                }
                not += "\n";
            }

            not += ((bg_service)mContext).getDistanceDebug();
        } else {
            int detection_on = 0;
            //Log.i(getString(R.string.debug_id),"we have "+String.valueOf(areas.size())+" areas");
            for (int i = 0; i < areas.size(); i++) {
                if (areas.get(i).getDetection() >= 1) {
                    detection_on++;
                }
            }
            not = String.valueOf(detection_on) + "/" + String.valueOf(areas.size()) + " Areas protected";
        }
        return not;
    }
}
