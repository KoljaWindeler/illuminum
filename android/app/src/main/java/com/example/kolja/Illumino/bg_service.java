package com.example.kolja.Illumino;

import android.app.AlarmManager;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.media.AudioManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.IBinder;
import android.os.PowerManager;
import android.os.PowerManager.WakeLock;
import android.os.Vibrator;
import android.support.v4.app.NotificationCompat;
import android.telephony.TelephonyManager;
import android.util.Log;

import org.java_websocket.util.Base64;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

import de.tavendo.autobahn.WebSocketConnection;
import de.tavendo.autobahn.WebSocketException;
import de.tavendo.autobahn.WebSocketHandler;

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
    public int getState()       {           return this.state;       }
    public Location getCoordinates() {      return this.coordinates;    }
}

class coordinate{
    private Location last_valid_location;
    private boolean valid=false;

    public coordinate()                     { super();    }
    public void setCoordinaes(Location loc) { this.last_valid_location=loc; valid=true;  }
    public Location getCoordinaes()         { return this.last_valid_location;   }
    public boolean isValid()                { return this.valid;   }
}

public class bg_service extends Service {
    public static final String LOG = "LOG";
    public static final String JSON = "JSON";
    public static final String NOTIFICATION = "BG_RECEIVER";
    public static final String SENDER = "BG_SENDER";
    public static final String ACTION_PING = "illumino.ACTION_PING";
    public static final String ACTION_CONNECT = "illumino.ACTION_CONNECT";
    public static final String ACTION_SHUT_DOWN = "illumino.ACTION_SHUT_DOWN";

    private IBinder mBinder;
    private AudioManager am;
    private Vibrator v;
    private SharedPreferences settings;
    private Handler mHandler;
    private LocationManager mLocationManager;
    private NotificationManager mNotificationManager = null;
    private NotificationCompat.Builder mNotificationBuilder = new NotificationCompat.Builder(this);
    private WebSocketConnection mWebSocketClient;
    private String mNetworkType=null;
    private AlarmManager mAlarmManager;
    private PendingIntent mPendingIntentCreator;

    private ArrayList<area> areas = new ArrayList<area>();
    private ArrayList<String> msg_out = new ArrayList<String>();

    // debugging
    private String distance_debug = "";

    private coordinate last_known_location=new coordinate();
    private Bitmap last_picture = null;
    private String area_of_last_alert = "";
    private String time_of_last_alert = "";
    private long last_ts_in;
    private long last_ts_out;

    private int server_told_location = -1;
    private boolean mShutDown;
    private boolean mLoggedIn;
    private boolean mConnected;
    private Context mContext;

    // intents to restart us with
    // plain
    public static Intent startIntent(Context context){
        Intent i = new Intent(context, bg_service.class);
        i.setAction(ACTION_CONNECT);
        return i;
    }

    private Runnable delayed_reconnect=new Runnable() {
        @Override
        public void run() {
            startService(startIntent(mContext));
        }
    };

    // initiates a hb send
    public static Intent pingIntent(Context context){
        Intent i = new Intent(context, bg_service.class);
        i.setAction(ACTION_PING);
        return i;
    }


    // to kill us
    public static Intent closeIntent(Context context){
        Intent i = new Intent(context, bg_service.class);
        i.setAction(ACTION_SHUT_DOWN);
        return i;
    }



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
                .setSmallIcon(R.drawable.logobw)
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

        if(mConnected) {
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

                    //Log.i(getString(R.string.debug_id), object.toString());
                    //console.log(JSON.stringify(cmd_data));
                    send_msg(object.toString());

                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }

            // update once we've change our position, just for the DUBUG line!!
            showNotification("Illumino check location", Notification_text_builder(false), Notification_text_builder(true));
        }
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
    // https://github.com/schwiz/android-websocket-example/blob/master/src/net/schwiz/eecs780/PushService.java
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        //try {
        //    Thread.sleep(10000);
        //} catch (Exception ex) {   }


        WakeLock wakelock = ((PowerManager) getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Illumino Service");
        wakelock.acquire();

        mShutDown = false;
        mLoggedIn = false;
        mContext = this;
        mHandler = new Handler();

        write_to_file("this is on start");
        // get services
        am = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        settings = (SharedPreferences) getSharedPreferences(MainActivity.PREFS_NAME, 0);
        mAlarmManager = (AlarmManager)getSystemService(Context.ALARM_SERVICE);
        mPendingIntentCreator = PendingIntent.getService(this, 0, bg_service.pingIntent(this), PendingIntent.FLAG_UPDATE_CURRENT);

        // establish comm interface
        registerReceiver(receiver, new IntentFilter(bg_service.SENDER));
        registerReceiver(receiver, new IntentFilter(android.net.ConnectivityManager.CONNECTIVITY_ACTION));

        // Register the listener with the Location Manager to receive location updates
        mLocationManager = (LocationManager) this.getSystemService(Context.LOCATION_SERVICE);
        mLocationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 0, 0, locationListener);

        setupNotifications();

        // start loop
        boolean recreate=false;
        write_to_file("check if we should recreate");
        if(mWebSocketClient == null){
            recreate=true;
            write_to_file("yes, or client is set to null");
        } else if(!mWebSocketClient.isConnected()) {
            recreate = true;
            write_to_file("yes, is not connected");
        } else if(!mConnected){
            recreate = true;
            write_to_file("yes, mConnected said so");
        }
        if(intent!=null) {
            if (ACTION_CONNECT.equals(intent.getAction())) {
                recreate = true;
                write_to_file("yes, this is ACTION CONNECT");
            } else if(ACTION_PING.equals(intent.getAction())){
                write_to_file("this is ACTION PING");
            }
        } else {
            write_to_file("this is NO ACTION");
        }

        try {
            if (recreate) {
                showNotification("Illumino", "connecting..", "");
                write_to_file("not connected, try to reconnect");
                createWebSocket(); // create a new websockets, reuse is forbidden
            } else {
                write_to_file("connection seams to be fine");
            }
        } catch (Exception ex){
            write_to_file("exeption on connect:" + ex.toString());
        }

        if(intent!=null){
            if(ACTION_PING.equals(intent.getAction())){
                if(mWebSocketClient!=null && mWebSocketClient.isConnected()) {
                    JSONObject object = new JSONObject();
                    try {
                        object.put("cmd", "hb");
                    } catch (JSONException e) {
                        write_to_file("exeption on put hb to JSON");
                        e.printStackTrace();
                    }
                    send_msg(object.toString());
                    last_ts_out=System.currentTimeMillis();
                }
            }
        }

        if(intent == null || (intent.getAction()!=null && !intent.getAction().equals(ACTION_SHUT_DOWN)) || (intent.getAction()==null)){
            PendingIntent operation = PendingIntent.getService(this, 0, bg_service.pingIntent(this), PendingIntent.FLAG_NO_CREATE);
            if(operation == null) {
                mAlarmManager.setInexactRepeating(AlarmManager.RTC_WAKEUP, System.currentTimeMillis(), 60000, mPendingIntentCreator);
                write_to_file("wakeup for ping scheduled for now+60sec");
            } else {
                write_to_file("there is a pending intent");
            }
        }

        wakelock.release();
        return Service.START_STICKY;
    }

    private void write_to_file(String started) {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss");
        started=sdf.format(new Date())+" "+started+"\n";

        String baseFolder="";
        // check if external storage is available
        if(Environment.getExternalStorageState().equals(Environment.MEDIA_MOUNTED)) {
            baseFolder = mContext.getExternalFilesDir(null).getAbsolutePath();
        }
        // revert to using internal storage
        else {
            baseFolder = mContext.getFilesDir().getAbsolutePath();
        }

        File file = new File(baseFolder + "bg_service.txt");
        FileOutputStream fos = null;
        try {
            fos = new FileOutputStream(file,true);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        try {
            fos.write(started.getBytes());
        } catch (IOException e) {
            e.printStackTrace();
        }
        try {
            fos.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
        // debug output
        Log.i(getString(R.string.debug_id),started);
    }

    @Override
    public IBinder onBind(Intent arg0) {
        return mBinder;
    }

    private BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            try {
                if (intent != null && intent.getExtras() != null) {

                    Bundle bundle = intent.getExtras();
                    if (bundle != null) {
                        String data = bundle.getString(bg_service.JSON,"");
                        if(!data.equals("")) {
                            send_msg(data);
                        }
                    }


                    final ConnectivityManager connectivityManager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
                    final NetworkInfo ni = connectivityManager.getActiveNetworkInfo();

                    if (ni != null && ni.isConnectedOrConnecting()) {
                        if(mNetworkType!=null && !mNetworkType.equals(ni.getTypeName())) {
                            write_to_file("Network was "+mNetworkType+" and changed to " + ni.getTypeName()+ " calling restart ");
                            restart_connection();
                        }
                        mNetworkType=ni.getTypeName();
                    } else if (intent.getBooleanExtra(ConnectivityManager.EXTRA_NO_CONNECTIVITY, Boolean.FALSE)) {
                        write_to_file("There's no network connectivity");
                    }
                }
            }
            catch (Exception ex){
                write_to_file("catched this on receiving "+ex.toString());
            }
        }
    };
    ///////////////////////////////////////////////////////////////////////////////
    /////////////////////////////// android app stuff /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////// web socket handling /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
    private void createWebSocket() {

        final String wsuri = "ws://172.12.213.117:10820";

        try {
            last_ts_in=0;
            write_to_file("Setting up WebSocket and connecting");
            mWebSocketClient = new WebSocketConnection();
            mWebSocketClient.connect(wsuri, new WebSocketHandler() {
                // websocket is connected and has just opened
                @Override
                public void onOpen() {
                    write_to_file("Socket Opened");
                    mConnected = true;
                    // on open -> login in.
                    JSONObject object = new JSONObject();
                    try {
                        object.put("cmd", "prelogin");
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                    write_to_file("sending as socket is open: " + object.toString());
                    send_msg(object.toString());
                }

                // websocket is connected and we've just received a message
                @Override
                public void onTextMessage(String message) {
                    write_to_file("onMessage: " + message);

                    read_msg(message);
                }

                @Override
                public void onClose(int code, String reason) {
                    write_to_file("On Closed " + reason);
                    restart_connection();
                }
            });
        }

        catch (WebSocketException e){
            write_to_file("On Error " + e.getMessage());
            restart_connection();
        }
    }

    // restart
    private void restart_connection(){
        mWebSocketClient=null;
        mConnected = false;
        showNotification("Illumino", "disconnected", "");

        try{
            mAlarmManager.cancel(mPendingIntentCreator);
        } catch (Exception ex){

        }

        mHandler.removeCallbacks(delayed_reconnect);
        mHandler.postDelayed(delayed_reconnect,5000); // start in 5 sec
    }


    // handle message that came in
    private void read_msg(String message){
        WakeLock wakelock = ((PowerManager) getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Illumino");
        wakelock.acquire();
        last_ts_in = System.currentTimeMillis();

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
                    TelephonyManager tManager = (TelephonyManager)getSystemService(Context.TELEPHONY_SERVICE);
                    String uuid = tManager.getDeviceId();

                    String login = settings.getString("LOGIN", "Kolja");
                    String pw = settings.getString("PW", "hui");
                    o_snd.put("cmd", "login");
                    o_snd.put("login", login);
                    o_snd.put("uuid", uuid);
                    o_snd.put("pw", pw);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
                write_to_file("received prelogin, sending " + o_snd.toString());
                //console.log(JSON.stringify(cmd_data));
                send_msg(o_snd.toString());
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // if we receive a login answer, we should check if we can answer with a location
            else if (cmd.equals("login")) {
                if (o_recv.getString("ok").equals("1")) {
                    write_to_file("We are logged in!");
                    mLoggedIn = true;

                    // assuming we reconnected as a reaction on a server reboot, the server has no idea where we are. we should tell him right away if we know it
                    if (last_known_location.isValid()) {
                        write_to_file("i have a valid location");
                        check_locations(last_known_location.getCoordinaes());
                    }


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
                            //write_to_file("state:" + String.valueOf(o_recv.getInt("state")) + " " + String.valueOf(o_recv.getInt("detection")));
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
                    String name = o_recv.getString("area");
                    Integer det = o_recv.getInt("detection");
                    Location new_loc = new Location("new");
                    if (!o_recv.getString("latitude").equals("") && !o_recv.getString("longitude").equals("")) {
                        new_loc.setLatitude(Float.parseFloat(o_recv.getString("latitude")));
                        new_loc.setLongitude(Float.parseFloat(o_recv.getString("longitude")));
                    } else {
                        new_loc.setLatitude(0.0);
                        new_loc.setLongitude(0.0);
                    }

                    int state = -1;
                    if (o_recv.has("state")) {
                        state = o_recv.getInt("state");
                    }

                    // add it to the structure
                    areas.add(new area(name, det, new_loc, 500, state));
                }

                // show notification
                showNotification("Illumino read message", Notification_text_builder(false), Notification_text_builder(true));
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // receive a image
            else if (cmd.equals("rf")) {
                byte[] decodedString = Base64.decode(o_recv.getString("img"), Base64.NO_OPTIONS);
                last_picture = BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length); // todo: we need a kind of, if app has started reset picture to null
                SimpleDateFormat sdf = new SimpleDateFormat("HH:mm");
                time_of_last_alert = sdf.format(new Date());
                // show notification
                showNotification("Illumino read file", Notification_text_builder(false), "");
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // receive a heartbeat answer
            //else if (cmd.equals("hb")){
            else if (cmd.equals("shb")) {
                try {
                    o_snd.put("cmd", "shb");
                    o_snd.put("ok", 1);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
                //Log.i(getString(R.string.debug_id), o_snd.toString());
                //console.log(JSON.stringify(cmd_data));
                send_msg(o_snd.toString());
            }

        } catch (Exception e) {
            write_to_file("Error on decoding incoming message " + e.getMessage());
        }
        wakelock.release();
    }

    // send a message or put it in the buffer
    private void send_msg(String input) {
        // check if we are dis-connected
        //write_to_file("on send");
        if (!input.equals("")) {
            msg_out.add(input);
        }

        try {
            if (mWebSocketClient == null || !mConnected || !mWebSocketClient.isConnected() || (last_ts_in>0 && last_ts_in < last_ts_out)) {
                String s="";
                if(mWebSocketClient == null){
                    s+=" mWebSocketClient is null ";
                }

                if(!mConnected){
                    s+=" mConnected is false ";
                }

                if(!mWebSocketClient.isConnected()){
                    s+=" mwebsocketclient is not connected ";
                }

                if((last_ts_in>0 && last_ts_in < last_ts_out)){
                    s+=String.valueOf(last_ts_in)+"<"+String.valueOf(last_ts_out);
                }


                write_to_file("I don't think we are still connected, as " + s);
                restart_connection();
            }
        }catch (Exception ex){
            write_to_file("Exception on check if client is connected in send_msg!! " + ex.toString());
        }


        // if we are still connected: send
        if(mConnected){
        //else {
            try {
                while (msg_out.size() > 0) {
                    //write_to_file("on send websocket");
                    mWebSocketClient.sendTextMessage(msg_out.get(0));
                    msg_out.remove(0);
                }
            } catch(Exception ex){
                write_to_file("Exception on send -->" + ex.toString());
                restart_connection();
            }
        }
    }
    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////// web socket handling /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
}