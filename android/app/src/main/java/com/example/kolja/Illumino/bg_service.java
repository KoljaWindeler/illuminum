package com.example.kolja.Illumino;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import android.content.SharedPreferences;
import android.media.AudioManager;
import android.os.Vibrator;
import android.graphics.Bitmap;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.util.Log;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.support.v4.app.NotificationCompat;
import java.text.SimpleDateFormat;
import java.util.Date;
import android.content.Context;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.java_websocket.util.Base64;
import org.json.JSONException;
import org.json.JSONObject;
import android.content.BroadcastReceiver;
import android.content.IntentFilter;
import android.os.PowerManager;
import android.os.PowerManager.WakeLock;

class area{
    private String name;
    private Integer detection;
    private Location coordinates;
    private Integer distance;
    private Integer state; // debugging

    public area(String name, Integer detection, Location coordinates, Integer distance, Integer state){
        super();
        this.name=name;
        this.detection=detection;
        this.coordinates=coordinates;
        this.distance=distance;
        this.state=state;
    }

    public void setState(int st) {          this.state=st;              }
    public void setDetection(int det){      this.detection=det;         }
    public int getCriticalDistance(){       return this.distance;       }
    public int getDetection()   {           return this.detection;      }
    public String getName()     {           return this.name;           }
    public int getState()       {           return this.distance;       }
    public Location getCoordinates() {      return this.coordinates;    }
}

class coordinate{
    private Location last_valid_location;
    private boolean valid=false;

    public coordinate()                     { super();    }
    public void setCoordinaes(Location loc) { this.last_valid_location=loc; valid=true;  };
    public Location getCoordinaes()         { return this.last_valid_location;   };
    public boolean isValid()                { return this.valid;   }
}

public class bg_service extends Service {
    public static final String LOG = "LOG";
    public static final String JSON = "JSON";
    public static final String NOTIFICATION = "BG_RECEIVER";
    public static final String SENDER = "BG_SENDER";
    private static final String ACTION_CONNECT = "connect";

    private IBinder mBinder;
    private final NotificationCompat.Builder mNotificationBuilder = new NotificationCompat.Builder(this);
    private AudioManager am;
    private Vibrator v;
    private SharedPreferences settings;


    private ArrayList<area> areas = new ArrayList<area>();
    private ArrayList<String> msg_out = new ArrayList<String>();

    // debugging
    private String distance_debug = "";


    private WebSocketClient mWebSocketClient;
    private LocationManager locationManager;
    private NotificationManager mNotificationManager = null;
    private coordinate last_known_location=new coordinate();
    private Bitmap last_picture = null;
    private String area_of_last_alert = "";
    private String time_of_last_alert = "";
    private long last_ts_in;

    private int server_told_location = -1;
    private boolean mShutDown;
    private boolean mLoggedIn;


    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////////// notification ////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
    private void setupNotifications() { //called in onCreate()
        if (mNotificationManager == null) {
            mNotificationManager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        }
        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, new Intent(this, MainActivity.class).setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP), 0);
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

    private void showNotification(String title, String short_text, String long_text) {
        if (last_picture == null) {
            String login = settings.getString("LOGIN", "Kolja");
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

    private void showNotification(String title, String short_text, Bitmap picture) {
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

    private String Notification_text_builder(boolean l_t) {
        String not = "";
        if (l_t) {
            for (int i = 0; i < areas.size(); i++) {
                not += areas.get(i).getName() + ": ";
                if(areas.get(i).getDetection() >= 1) {
                    not += "Detection on";
                } else {
                    not += "Detection off";
                }

                if (areas.get(i).getState() >= 1) {
                    not += " / Movement";
                } else {
                    not += " / No Movement";
                }
                not += "\n";
            }
            not += distance_debug;
        } else {
            int detection_on = 0;
            //Log.i("Websocket","we have "+String.valueOf(areas.size())+" areas");
            for (int i = 0; i < areas.size(); i++) {
                if (areas.get(i).getDetection() >= 1) {
                    detection_on++;
                }
            }
            not = String.valueOf(detection_on) + "/" + String.valueOf(areas.size()) + " Areas protected";
        }
        return not;
    }
    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////////// notification ////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////////
    ////////////////////////////// location gedönese //////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
    private void check_locations(Location location) {
        last_known_location.setCoordinaes(location);
        int closest_area = -1;

        // debug
        distance_debug = "Distance Debug\n";

        // find closest area to our coordinates
        for (int i = 0; i < areas.size(); i++) {
            float this_distance = areas.get(i).getCoordinates().distanceTo(last_known_location.getCoordinaes());

            // debug
            distance_debug += "Area:" + areas.get(i).getName() + ", " + String.valueOf(this_distance) + "m\n";

            // check if we are IN a region
            if (this_distance < areas.get(i).getCriticalDistance()) {
                // lets see if we are even closer to the coordinates then the others
                if (closest_area == -1) {
                    closest_area = i;
                } else { // so we had already a "close area"
                    // see if we are even closer to this one
                    if (this_distance < areas.get(closest_area).getCoordinates().distanceTo(last_known_location.getCoordinaes())){
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
                    object.put("loc", areas.get(closest_area).getName());
                }

                Log.i("websocket", object.toString());
                //console.log(JSON.stringify(cmd_data));
                send_msg(object.toString());

            } catch (JSONException e) {
                e.printStackTrace();
            }
        }

        // update once we've change our position, just for the DUBUG line!!
        showNotification("Illumino", Notification_text_builder(false), Notification_text_builder(true));
    }

    ;

    // Define a listener that responds to location updates
    LocationListener locationListener = new LocationListener() {
        public void onLocationChanged(Location location) {
            check_locations(location);
        }

        public void onStatusChanged(String provider, int status, Bundle extras) {
        }

        public void onProviderEnabled(String provider) {
        }

        public void onProviderDisabled(String provider) {
        }
    };
    ///////////////////////////////////////////////////////////////////////////////
    ////////////////////////////// location gedönese //////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////////
    /////////////////////////////// android app stuff /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
    public static Intent pingIntent(Context context){
        Intent i = new Intent(context, bg_service.class);
        i.setAction(ACTION_CONNECT);
        return i;
    }

    // https://github.com/schwiz/android-websocket-example/blob/master/src/net/schwiz/eecs780/PushService.java
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        WakeLock wakelock = ((PowerManager) getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "EECS780 Service");
        wakelock.acquire();
        Log.i("websocket", "this is on start");
        mShutDown = false;
        mLoggedIn = false;

        // get services
        am = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        settings = (SharedPreferences) getSharedPreferences(MainActivity.PREFS_NAME, 0);

        // establish comm interface
        registerReceiver(receiver, new IntentFilter(bg_service.SENDER));

        // Register the listener with the Location Manager to receive location updates
        locationManager = (LocationManager) this.getSystemService(Context.LOCATION_SERVICE);
        locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 0, 0, locationListener);

        // start loop
        //t.start();
        connectWebSocket();

        setupNotifications();
        showNotification("Illumino", "connecting..", "");


        wakelock.release();
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
    ///////////////////////////// web socket handling /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
    Thread t = new Thread(new Runnable() {
        public void run() {
            Log.i("websocket", "Starting thread T");
            int count = 1;
            while (true) {
                try {
                    // check connetion
                    connectWebSocket();
                    if((System.currentTimeMillis() - last_ts_in) > 130000) {
                        Log.i("websocket", "not connected - reconnecting");
                        mWebSocketClient=null;
                        connectWebSocket();
                    }

                    // timeout timer
                    count++;
                    try {
                        Thread.sleep(3000);
                    } catch (Exception ex) {
                        Log.i("websocket", "exeption on wait");
                    }

                    // DEBUG
                    showNotification("Illumino " + String.valueOf(count) + "/20 " + String.valueOf((int) ((System.currentTimeMillis() - last_ts_in) / 1000)), Notification_text_builder(false), Notification_text_builder(true));

                    // send heartbeet to server every 60 sec
                    if (count > 19) {
                        count = 0;
                        JSONObject object = new JSONObject();
                        try {
                            object.put("cmd", "hb");
                        } catch (JSONException e) {
                            Log.i("websocket", "exeption on put hb");
                            e.printStackTrace();
                        }
                        Log.i("websocket", object.toString());
                        //console.log(JSON.stringify(cmd_data));

                        send_msg(object.toString());
                        // show notification
                        showNotification("Illumino", Notification_text_builder(false), Notification_text_builder(true));
                    }
                } catch (Exception ex){
                    Log.i("websocket", "!!!!!!!!!!!!!!!!!!!!!exeption !!!!!!!!!!!!!!!!!");
                    ex.printStackTrace();
                }
            }
        }
    });

    private void connectWebSocket() {
        // check if var is initialized
        URI uri=null;
        boolean recreate=false;
        if (mWebSocketClient == null) {
            recreate = true;
            Log.i("Websocket", "mWebsocketClient is null, recreating");
        } else if(!mWebSocketClient.getConnection().isOpen()) {
            mWebSocketClient.close();
            recreate = true;
            Log.i("Websocket", "mWebsocketClient has no open connection recreating");
        }

        if(recreate){
            try {
                uri = new URI("ws://172.12.213.117:10820");
            } catch (URISyntaxException e) {
                Log.i("Websocket", "URI execption!");
                e.printStackTrace();
                return;
            }

            mWebSocketClient = new WebSocketClient(uri) {
                // websocket is connected and has just opened
                @Override
                public void onOpen(ServerHandshake serverHandshake) {
                    Log.i("Websocket", "Opened");
                    // on open -> login in.
                    JSONObject object = new JSONObject();
                    try {
                        object.put("cmd", "prelogin");
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                    Log.i("websocket", object.toString());
                    send_msg(object.toString());
                }

                // websocket is connected and we've just received a message
                @Override
                public void onMessage(String message) {
                    Log.i("Websocket", "onMessage: " + message);
                    WakeLock wakelock = ((PowerManager) getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Illumino");
                    wakelock.acquire();

                    // forward message to possible listening apps
                    Intent intent = new Intent(NOTIFICATION);
                    intent.putExtra(JSON, message);
                    sendBroadcast(intent);

                    // but check if we could use it
                    String cmd;
                    try {
                        JSONObject o_recv = new JSONObject(message);
                        JSONObject o_snd = new JSONObject();
                        cmd = o_recv.getString("cmd");

                        //////////////////////////////////////////////////////////////////////////////////////
                        // if we receive a prelogin answer, we have to calc our login and send it to the server
                        if (cmd.equals("prelogin")) {
                            try {
                                String login = settings.getString("LOGIN", "Kolja");
                                String pw = settings.getString("PW", "hui");
                                o_snd.put("cmd", "login");
                                o_snd.put("login", login);
                                o_snd.put("pw", pw);
                            } catch (JSONException e) {
                                e.printStackTrace();
                            }
                            Log.i("websocket", o_snd.toString());
                            //console.log(JSON.stringify(cmd_data));
                            send_msg(o_snd.toString());
                        }

                        //////////////////////////////////////////////////////////////////////////////////////
                        // if we receive a login answer, we should check if we can answer with a location
                        else if (cmd.equals("login")) {
                            if (o_recv.getString("ok").equals("1")) {
                                Log.i("websocket", "We are logged in!");
                                mLoggedIn = true;

                                // assuming we reconnected as a reaction on a server reboot, the server has no idea where we are. we should tell him right away if we know it
                                if (last_known_location.isValid()) {
                                    Log.i("websocket", "i have a valid location");
                                    check_locations(last_known_location.getCoordinaes());
                                }
                                last_ts_in = System.currentTimeMillis();

                                // check if we have messages in the q
                                send_msg("");
                            }
                        }

                        //////////////////////////////////////////////////////////////////////////////////////
                        // update our list of areas
                        else if (cmd.equals("m2v_login") || cmd.equals("detection_changed") || cmd.equals("state_change")) {
                            int found = 0;
                            for (int i = 0; i < areas.size(); i++) {
                                if (areas.get(i).getName().equals(o_recv.getString("area"))) {
                                    found = 1;
                                    areas.get(i).setDetection(o_recv.getInt("detection"));

                                    if (o_recv.has("state")) {
                                        Log.i("websockets", "state:" + String.valueOf(o_recv.getInt("state")) + " " + String.valueOf(o_recv.getInt("detection")));
                                        if (o_recv.getInt("state") == 1 && o_recv.getInt("detection") >= 1) {
                                            if (am.getRingerMode() != AudioManager.RINGER_MODE_SILENT) {
                                                v.vibrate(500);
                                            }
                                            area_of_last_alert = o_recv.getString("area");
                                        }
                                        areas.get(i).setState(o_recv.getInt("state"));
                                    }
                                }
                            }

                            // first sign up .. add to list
                            if (found == 0) {
                                Log.i("Websocket", "added a new area");
                                String name=o_recv.getString("area");
                                Log.i("Websocket", "add det");
                                Integer det=o_recv.getInt("detection");
                                Log.i("Websocket", "get location");
                                Location new_loc = new Location("new");
                                if (!o_recv.getString("latitude").equals("") && !o_recv.getString("longitude").equals("")) {
                                    new_loc.setLatitude(Float.parseFloat(o_recv.getString("latitude")));
                                    new_loc.setLongitude(Float.parseFloat(o_recv.getString("longitude")));
                                } else {
                                    new_loc.setLatitude(0.0);
                                    new_loc.setLongitude(0.0);
                                }


                                Log.i("Websocket", "add location");
                                int state=-1;
                                if (o_recv.has("state")) {
                                    state=o_recv.getInt("state");
                                }

                                // add it to the structure
                                areas.add(new area(name,det,new_loc,500,state));
                            }

                            // show notification
                            showNotification("Illumino", Notification_text_builder(false), Notification_text_builder(true));
                        }

                        //////////////////////////////////////////////////////////////////////////////////////
                        // receive a image
                        else if (cmd.equals("rf")) {
                            byte[] decodedString = Base64.decode(o_recv.getString("img"), Base64.NO_OPTIONS);
                            last_picture = BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length); // todo: we need a kind of, if app has started reset picture to null
                            SimpleDateFormat sdf = new SimpleDateFormat("HH:mm");
                            time_of_last_alert = sdf.format(new Date());
                            // show notification
                            showNotification("Illumino", Notification_text_builder(false), "");
                        }

                        //////////////////////////////////////////////////////////////////////////////////////
                        // receive a heartbeat answer
                        else if (cmd.equals("hb")) {
                            last_ts_in = System.currentTimeMillis();
                        }

                        else if (cmd.equals("shb")) {
                            try {
                                o_snd.put("cmd", "shb");
                                o_snd.put("ok", 1);
                            } catch (JSONException e) {
                                e.printStackTrace();
                            }
                            Log.i("websocket", o_snd.toString());
                            //console.log(JSON.stringify(cmd_data));
                            send_msg(o_snd.toString());
                        }

                    } catch (Exception e) {
                        Log.i("Websocket", "Error " + e.getMessage());
                    }
                    wakelock.release();
                }

                @Override
                public void onClose(int i, String s, boolean b){
                    Log.i("Websocket", "Closed " + s);
                    showNotification("Illumino", "disconnected", "");
                    connectWebSocket();
                }

                @Override
                public void onError(Exception e) {
                    Log.i("Websocket", "Error " + e.getMessage());
                    showNotification("Illumino", "connection Error", "");
                    connectWebSocket();
                }
            };
            // connect
            mWebSocketClient.close();
            mWebSocketClient.connect();
        }
    }

    // send a message or put it in the buffer
    private void send_msg(String input) {
        // check if we are dis-connected
        if (mWebSocketClient == null || !mWebSocketClient.getConnection().isOpen()) {
            if (!input.equals("")) {
                msg_out.add(input);
            }
            connectWebSocket();
        }

        // if we are still connected: send
        else {
            if (!input.equals("")) {
                msg_out.add(input);
            }
            while (msg_out.size() > 0) {
                mWebSocketClient.send(msg_out.get(0));
                msg_out.remove(0);
            }
        }
    }
    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////// web socket handling /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
}