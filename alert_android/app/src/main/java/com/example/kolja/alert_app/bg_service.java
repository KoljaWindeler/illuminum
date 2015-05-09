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
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.text.ParseException;
import java.util.Date;
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

    private ArrayList<String> areas = new ArrayList<String>();
    private ArrayList<Integer> detection = new ArrayList<Integer>();
    private ArrayList<Location> det_area_coordinates = new ArrayList<Location>();
    private ArrayList<Integer> det_area_distances = new ArrayList<Integer>();

    // debugging
    private ArrayList<Integer> state = new ArrayList<Integer>(); // just for debugging
    private String distance_debug="";

    private WebSocketClient mWebSocketClient;
    private LocationManager locationManager;
    private NotificationManager mNotificationManager = null;
    private Location last_known_location;
    private int location_valid=0;
    private Bitmap last_picture = null;
    private String area_of_last_alert ="";
    private String time_of_last_alert ="";

    private int server_told_location =-1;
    private boolean connected=false;


    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////// web socket handling /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
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

                // on open -> login in.
                JSONObject object = new JSONObject();
                try {
                    //object.put("cmd", "login");
                    //object.put("login", "kolja_android");
                    //object.put("pw", "pw");
                    object.put("cmd", "prelogin");
                } catch (JSONException e) {
                    e.printStackTrace();
                }
                Log.i("websocket",object.toString());
                //console.log(JSON.stringify(cmd_data));
                mWebSocketClient.send(object.toString());
            }

            @Override
            public void onMessage(String message) {
                Log.i("Websocket", "onMessage: "+message);

                // forward message to possible listening apps
                Intent intent = new Intent(NOTIFICATION);
                intent.putExtra(JSON, message);
                sendBroadcast(intent);

                // but check if we could use it
                String cmd;
                JSONObject object = new JSONObject();

                try {
                    object = new JSONObject(message);
                    cmd = object.getString("cmd");

                    if(cmd.equals("prelogin")) {
                        JSONObject object_snd = new JSONObject();
                        try {
                            object_snd.put("cmd", "login");
                            object_snd.put("login", "kolja_android");
                            object_snd.put("pw", "pw");
                        } catch (JSONException e) {
                            e.printStackTrace();
                        }
                        Log.i("websocket", object_snd.toString());
                        //console.log(JSON.stringify(cmd_data));
                        mWebSocketClient.send(object_snd.toString());

                    } else if(cmd.equals("login")){
                        if(object.getString("ok").equals("1")){
                            Log.i("websocket", "We are logged in!");
                            connected=true;

                            // assuming we reconnected as a reaction on a server reboot, the server has no idea where we are. we should tell him right away if we know it
                            if(location_valid==1) {
                                Log.i("websocket", "i have a valid location");
                                check_locations(last_known_location);
                            }
                        }


                    } else if(cmd.equals("m2v_login") || cmd.equals("detection_changed") || cmd.equals("state_change")) {
                        int found=0;
                        for(int i=0;i<areas.size();i++){
                            if(areas.get(i).equals(object.getString("area"))){
                                found=1;
                                detection.set(i,object.getInt("detection"));

                                if(object.has("state")) {
                                    Log.i("websockets","state:"+String.valueOf(object.getInt("state"))+" "+String.valueOf(object.getInt("detection")));
                                    if(object.getInt("state")==1 && object.getInt("detection")>=1){
                                        Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
                                        v.vibrate(500);
                                        area_of_last_alert=object.getString("area");
                                    }
                                    state.set(i, object.getInt("state"));
                                }
                            }
                        }

                        // first sign up .. add to list
                        if(found==0){
                            Log.i("Websocket","added a new area");
                            areas.add(object.getString("area"));
                            Log.i("Websocket","add det");
                            detection.add(object.getInt("detection"));
                            Log.i("Websocket","get location");
                            Location new_loc = new Location("new");
                            if(!object.getString("latitude").equals("") && !object.getString("longitude").equals("")){
                                new_loc.setLatitude(Float.parseFloat(object.getString("latitude")));
                                new_loc.setLongitude(Float.parseFloat(object.getString("longitude")));
                            } else {
                                new_loc.setLatitude(0.0);
                                new_loc.setLongitude(0.0);
                            }


                            Log.i("Websocket","add location");
                            det_area_coordinates.add(new_loc);
                            det_area_distances.add(500);

                            if(object.has("state")) {
                                state.add(object.getInt("state"));
                            } else {
                                state.add(-1);
                            }
                        }

                        // show notification
                        showNotification("SmartCam",Notification_text_builder(false),Notification_text_builder(true));

                    } else if(cmd.equals("rf")){
                        byte[] decodedString = Base64.decode(object.getString("img"), Base64.NO_OPTIONS);
                        last_picture = BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length); // todo: we need a kind of, if app has started reset picture to null
                        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm");
                        time_of_last_alert=sdf.format(new Date());
                        // show notification
                        showNotification("SmartCam", Notification_text_builder(false), "");

                    }

                } catch (Exception e) {
                    cmd="";
                }
            }

            @Override
            public void onClose(int i, String s, boolean b) {
                Log.i("Websocket", "Closed " + s);
                connected=false;
                showNotification("SmartCam","disconnected","");
            }

            @Override
            public void onError(Exception e) {
                Log.i("Websocket", "Error " + e.getMessage());
                connected=false;
                showNotification("SmartCam","connection Error","");
            }
        };
        mWebSocketClient.connect();
    }

    Thread t = new Thread(new Runnable() {
        public void run() {
            int count = 1;
            while(true) {
                count ++;
                //Log.i("Websocket", "loop " + String.valueOf(count));
                try {
                    Thread.sleep(3000);
                } catch (Exception ex) {
                    ;
                }


                // send heartbeet to server every 60 sec
                if(count>=20){
                    count=0;
                    JSONObject object = new JSONObject();
                    try {
                        object.put("cmd", "hb");
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                    Log.i("websocket",object.toString());
                    //console.log(JSON.stringify(cmd_data));
                    mWebSocketClient.send(object.toString());
                }

                if(!connected){
                    Log.i("websocket", "not connected - reconnecting");
                    connectWebSocket();
                }
            }
        }
    });
    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////// web socket handling /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////////// notification ////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
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
    private void showNotification(String title,String short_text, String long_text) {
        if(last_picture==null) {
            mNotificationBuilder
                    .setContentTitle(title)
                            //.setContentInfo("shor first line, right")
                    .setContentText(short_text)
                    .setStyle(new NotificationCompat.BigTextStyle().bigText(long_text)); //.setSummaryText(short_text+"3"));this will be shown if you pull down the menu
            displayNotification();
        } else {
            String Message = "Alert at "+area_of_last_alert+" "+time_of_last_alert+"! "+short_text+".";
            showNotification(title, Message, last_picture);
        }
    }
    private void showNotification(String title,String short_text, Bitmap picture) {
        mNotificationBuilder
                .setContentTitle(title)
                .setContentText(short_text)
                .setStyle(new NotificationCompat.BigPictureStyle().bigPicture(picture).setSummaryText(short_text));
        displayNotification();
    }
    private void displayNotification(){
        if (mNotificationManager != null) {
            mNotificationManager.notify(1, mNotificationBuilder.build());
        }
    }
    private String Notification_text_builder(boolean l_t){
        String not="";
        if(l_t) {
            for(int i = 0; i < areas.size(); i++) {
                not += areas.get(i) + ": ";
                if (detection.get(i) >= 1) {
                    not += "Detection on";
                } else {
                    not += "Detection off";
                }

                if (state.get(i) >= 1) {
                    not += " / Movement";
                } else {
                    not += " / No Movement";
                }
                not += "\n";
            }
            not+= distance_debug;
        } else {
            int detection_on=0;
            //Log.i("Websocket","we have "+String.valueOf(areas.size())+" areas");
            for(int i = 0; i < areas.size(); i++) {
                if (detection.get(i)>=1) {
                    detection_on++;
                }
            }
            not=String.valueOf(detection_on)+"/"+String.valueOf(areas.size())+" Areas protected";
        }
        return not;
    }
    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////////// notification ////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////


    ///////////////////////////////////////////////////////////////////////////////
    /////////////////////////////// android app stuff /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
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
        showNotification("SmartCam","connecting..","");
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
    ///////////////////////////////////////////////////////////////////////////////
    /////////////////////////////// android app stuff /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////


    ///////////////////////////////////////////////////////////////////////////////
    ////////////////////////////// location gedönese //////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
    private void check_locations(Location location) {
        last_known_location = location;
        location_valid = 1;
        int closest_area = -1;

        // debug
        distance_debug="Distance Debug\n";

        // find closest area to our coordinates
        for (int i = 0; i < det_area_coordinates.size(); i++) {
            float this_distance = det_area_coordinates.get(i).distanceTo(last_known_location);

            // debug
            distance_debug+="Area:"+areas.get(i)+", "+String.valueOf(this_distance)+"m\n";

            // check if we are IN a region
            if (this_distance < det_area_distances.get(i)) {
                // lets see if we are even closer to the coordinates then the others
                if (closest_area == -1){
                    closest_area = i;
                } else if(closest_area >=0){
                    if(this_distance < det_area_distances.get(closest_area)) {
                        closest_area = i;
                    }
                }
            }
        }

        // check if we should tell the server
        if (server_told_location != closest_area) {
            server_told_location = closest_area;
            // we should

            // Intent intent = new Intent(NOTIFICATION);
            // intent.putExtra(LOG, "log");
            // intent.putExtra(JSON, distance);
            // sendBroadcast(intent);

            // tell the server that we are in that area
            JSONObject object = new JSONObject();
            try {
                object.put("cmd", "update_location");
                if (closest_area == -1) {
                    object.put("loc", "www");
                } else {
                    object.put("loc", areas.get(closest_area));
                }
                if (connected) {
                    Log.i("websocket", object.toString());
                    //console.log(JSON.stringify(cmd_data));
                    mWebSocketClient.send(object.toString());
                }
            } catch (JSONException e) {
                e.printStackTrace();
            }
        }

        // update once we've change our position, just for the DUBUG line!!
        showNotification("SmartCam",Notification_text_builder(false),Notification_text_builder(true));
    };

    // Define a listener that responds to location updates
    LocationListener locationListener = new LocationListener() {
        public void onLocationChanged(Location location) {            check_locations(location);        }
        public void onStatusChanged(String provider, int status, Bundle extras) {}
        public void onProviderEnabled(String provider) {}
        public void onProviderDisabled(String provider) {}
    };
    ///////////////////////////////////////////////////////////////////////////////
    ////////////////////////////// location gedönese //////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
}