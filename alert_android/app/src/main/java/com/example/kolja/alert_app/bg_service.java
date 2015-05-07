package com.example.kolja.alert_app;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import android.os.Vibrator;

import android.graphics.Bitmap;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.util.Log;

import android.app.Activity;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.graphics.BitmapFactory;
import android.graphics.drawable.Drawable;
import android.media.AudioManager;
import android.os.Bundle;
import android.support.v4.app.NotificationCompat;
import android.media.MediaPlayer;
import android.os.Bundle;
import android.os.Binder;
import android.os.Environment;
import android.os.Handler;
import android.os.IBinder;
import android.os.RemoteException;
import android.widget.ImageButton;
import android.widget.SeekBar;
import android.widget.TextView;

import java.io.File;
import java.io.IOException;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;


import android.app.ListActivity;
import android.content.ComponentName;
import android.content.ContentUris;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.database.Cursor;

import android.net.Uri;

import android.provider.MediaStore;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.view.animation.Animation;
import android.view.animation.AnimationUtils;
import android.view.animation.TranslateAnimation;
import android.view.animation.Animation;
import android.view.animation.Animation.AnimationListener;
import android.view.animation.AnimationUtils;
import android.widget.ImageView;
import android.widget.ListView;

import android.widget.SimpleCursorAdapter;


import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.java_websocket.util.Base64;
import org.json.JSONException;
import org.json.JSONObject;
import android.os.Bundle;
import android.content.Context;
import android.content.BroadcastReceiver;
import android.content.IntentFilter;

public class bg_service extends Service {
    public static final java.lang.String LOG = "LOG";
    public static final java.lang.String JSON = "JSON";
    public static final String NOTIFICATION = "alert_bg_receiver";
    public static final String SENDER = "alert_bg_sender";

    private IBinder mBinder;
    private final NotificationCompat.Builder mNotificationBuilder = new NotificationCompat.Builder(this);
    private ArrayList<String> list = new ArrayList<String>();
    private ArrayList<String> areas = new ArrayList<String>();
    private ArrayList<Integer> detection = new ArrayList<Integer>();
    private ArrayList<Integer> state = new ArrayList<Integer>();
    private WebSocketClient mWebSocketClient;
    private LocationManager locationManager;
    private NotificationManager mNotificationManager = null;
    private Location last_known_location;
    private int location_valid=0;

    private int loc_home =-1;
    private boolean connected=false;


    // web socket process
    private void connectWebSocket() {
        URI uri;
        try {
            uri = new URI("ws://172.12.213.117:10820");
        } catch (URISyntaxException e) {
            e.printStackTrace();
            return;
        }

        mWebSocketClient = new WebSocketClient(uri) {
            @Override
            public void onOpen(ServerHandshake serverHandshake) {
                Log.i("Websocket", "Opened");
                JSONObject object = new JSONObject();
                try {
                    object.put("cmd", "login");
                    object.put("login", "kolja_android");
                    object.put("pw", "pw");
                } catch (JSONException e) {
                    e.printStackTrace();
                }
                Log.i("websocket",object.toString());
                //console.log(JSON.stringify(cmd_data));
                mWebSocketClient.send(object.toString());
                connected=true;

                if(location_valid==1) {
                    Log.i("websocket", "i have a valid location");
                    loc_home=-1;
                    check_locations(last_known_location);
                }
            }

            @Override
            public void onMessage(String message) {
                Log.i("Websocket", "onMessage: "+message);

                // forward message to possible listen apps
                Intent intent = new Intent(NOTIFICATION);
                intent.putExtra(JSON, message);
                sendBroadcast(intent);

                // but check if we could use it
                String cmd;
                JSONObject object = new JSONObject();

                try {
                    object = new JSONObject(message);
                    cmd=object.getString("cmd");

                    if(cmd.equals("m2v_login") || cmd.equals("detection_changed") || cmd.equals("state_change")) {
                        int found=0;
                        for(int i=0;i<areas.size();i++){
                            if(areas.get(i).equals(object.getString("area"))){
                                found=1;
                                detection.set(i,object.getInt("detection"));
                                if(object.has("state")) {
                                    if(object.getInt("state")==1 && object.getInt("detection")==1){
                                        Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
                                        v.vibrate(100);
                                    }
                                    state.set(i, object.getInt("state"));
                                }
                                break;
                            }
                        }

                        if(found==0){
                            areas.add(object.getString("area"));
                            detection.add(object.getInt("detection"));
                            if(object.has("state")) {
                                state.add(object.getInt("state"));
                            } else {
                                state.add(-1);
                            }
                        }

                        String not="";
                        for(int i=0;i<areas.size();i++){
                            not+=areas.get(i)+": ";
                            if(detection.get(i)>=1){
                                not+="Detection on";
                            } else {
                                not+="Detection off";
                            }
                            Log.i("Websocket", "check if it has state");
                            not+=" state :"+String.valueOf(object.getString("state"));
                            not+="\n";
                        }
                        showNotification(not);
                    } else if(cmd.equals("rf")){
                        String encodedImage = object.getString("img");
                        Log.i("websocket", "got str from obj");
                        byte[] decodedString = Base64.decode(encodedImage, Base64.NO_OPTIONS);
                        Log.i("websocket", "decoded");
                        Bitmap decodedByte = BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length);
                        Log.i("websocket", "loaded bitmap");

                        NotificationCompat.BigPictureStyle notiStyle = new NotificationCompat.BigPictureStyle();
                        notiStyle.bigPicture(decodedByte);

                        mNotificationBuilder.setTicker("connected").setStyle(notiStyle);//.setContentTitle("Alert on area "+String.valueOf(object.getString("area")));

                        //.setContentText(msg);
                        if (mNotificationManager != null) {
                            mNotificationManager.notify(1, mNotificationBuilder.build());
                        }

                    }




                } catch (Exception e) {
                    cmd="";
                }
            }

            @Override
            public void onClose(int i, String s, boolean b) {
                Log.i("Websocket", "Closed " + s);
                connected=false;
            }

            @Override
            public void onError(Exception e) {
                Log.i("Websocket", "Error " + e.getMessage());
                connected=false;
            }
        };
        mWebSocketClient.connect();
    }

    Thread t = new Thread(new Runnable() {
        public void run() {
            int count = 1;
            while(true) {
                //count ++;
                //Log.i("Websocket", "loop " + String.valueOf(count));
                try {
                    Thread.sleep(3000);
                } catch (Exception ex) {
                    ;
                }
                //showNotification(String.valueOf(count));
                if(!connected){
                    showNotification("Lost connection");
                    Log.i("websocket", "not connected - reconnecting");
                    connectWebSocket();
                }
            }
        }
    });

    private void setupNotifications() { //called in onCreate()
        if (mNotificationManager == null) {
            mNotificationManager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        }
        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0,new Intent(this, MainActivity.class).setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP),0);
        //PendingIntent pendingCloseIntent = PendingIntent.getActivity(this, 0,new Intent(this, MainActivity.class).setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP),0);
        mNotificationBuilder
                .setSmallIcon(R.drawable.webcam)
                .setCategory(NotificationCompat.CATEGORY_SERVICE)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setContentTitle("app is running")
                .setWhen(System.currentTimeMillis())
                .setContentIntent(pendingIntent)
                //.addAction(android.R.drawable.ic_menu_close_clear_cancel,"exit", pendingCloseIntent)
                .setOngoing(true);
    }


    private void showNotification(String msg) {
        mNotificationBuilder
                .setContentTitle("connected")
                .setStyle(new NotificationCompat.BigTextStyle().bigText(msg));
                //.setContentText(msg);
        if (mNotificationManager != null) {
            mNotificationManager.notify(1, mNotificationBuilder.build());
        }
    }



    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.i("websocket", "this is on start");

        // establish comm interface
        registerReceiver(receiver, new IntentFilter(bg_service.SENDER));

        // Register the listener with the Location Manager to receive location updates
        locationManager= (LocationManager) this.getSystemService(Context.LOCATION_SERVICE);
        locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 0, 0, locationListener);

        // start loop
        t.start();

        setupNotifications();
        showNotification("");
        //connectWebSocket();

        return Service.START_STICKY;
    }

    @Override
    public IBinder onBind(Intent arg0) {
        return mBinder;
    }

    private BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Bundle bundle = intent.getExtras();
            if (bundle != null) {
                String data = bundle.getString(bg_service.JSON);
                mWebSocketClient.send(data);
            }
        }
    };





    private void check_locations(Location location){
        last_known_location=location;
        location_valid=1;
        Location home = new Location("point B");
        home.setLatitude(30.1811);
        home.setLongitude(-95.47586);
        float distance = home.distanceTo(location);

        Intent intent = new Intent(NOTIFICATION);
        intent.putExtra(LOG, "log");
        intent.putExtra(JSON, distance);
        sendBroadcast(intent);

        JSONObject object = new JSONObject();
        try {
            object.put("cmd", "update_location");
            int fire=0;

            if(distance>500 && loc_home !=0){
                object.put("loc", "www"); // 2 perma fire, 1 regular
                loc_home =0;
                fire=1;
            } else if(distance<500 && loc_home !=1) {
                object.put("loc", "home"); // 0 off
                loc_home = 1;
                fire=1;
            }

           if(fire==1 && connected) {
               Log.i("websocket", object.toString());
               //console.log(JSON.stringify(cmd_data));
               mWebSocketClient.send(object.toString());
           }

        } catch (JSONException e) {
            e.printStackTrace();
        }

    }



    // Define a listener that responds to location updates
    LocationListener locationListener = new LocationListener() {
        public void onLocationChanged(Location location) {            check_locations(location);        }
        public void onStatusChanged(String provider, int status, Bundle extras) {}
        public void onProviderEnabled(String provider) {}
        public void onProviderDisabled(String provider) {}
    };



}