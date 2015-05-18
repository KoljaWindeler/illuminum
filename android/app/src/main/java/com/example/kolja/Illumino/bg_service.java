package com.example.kolja.Illumino;

import android.app.AlarmManager;
import android.app.NotificationManager;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.graphics.BitmapFactory;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.media.AudioManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.PowerManager;
import android.os.PowerManager.WakeLock;
import android.os.Vibrator;
import android.telephony.TelephonyManager;
import android.widget.Toast;

import org.java_websocket.util.Base64;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;

import de.tavendo.autobahn.WebSocketConnection;
import de.tavendo.autobahn.WebSocketException;
import de.tavendo.autobahn.WebSocketHandler;

class area{
    private String name;
    private Integer detection;
    private Location coordinates;
    private Integer range;
    private Integer state; // debugging

    public area(String name, Integer detection, Location coordinates, Integer range, Integer state){
        super();
        this.name=name;                 // like "home"
        this.detection=detection;       // 0=off, 1=on, 2=fast fire
        this.coordinates=coordinates;   // a android location
        this.range = range;         // range around the center
        this.state=state;
    }

    public void setState(int st) {          this.state=st;              }
    public void setDetection(int det){      this.detection=det;         }
    public int getCriticalRange(){          return this.range;       }
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


    private IBinder mBinder;
    private AudioManager am;
    private Vibrator v;
    private SharedPreferences settings;
    private Handler mHandler;
    private LocationManager mLocationManager;
    private s_notify mNofity = null;
    private s_wakeup mWakeup = null;
    private s_debug mDebug = null;
    private WebSocketConnection mWebSocketClient;
    private String mNetworkType=null;
//    private AlarmManager mAlarmManager=null;

    private ArrayList<area> areas = new ArrayList<area>();
    private ArrayList<String> msg_out = new ArrayList<String>();

    // debugging
    private String distance_debug = "";

    private coordinate last_known_location=new coordinate();
    private long last_ts_in;
    private long last_ts_out;

    private int server_told_location = -1;
    private boolean mShutDown;
    private boolean mLoggedIn;
    private boolean mConnected;
    private Context mContext;


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
            if (this_distance < areas.get(i).getCriticalRange()) {
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

        if(mConnected && mLoggedIn) {
            // check if we should tell the server
            if (server_told_location != closest_area) {
                server_told_location = closest_area;
                // we should

                // Intent intent = new Intent(NOTIFICATION);
                // intent.putExtra(LOG, "log");
                // intent.putExtra(JSON, range);
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
            mNofity.showNotification("Illumino check location", mNofity.Notification_text_builder(false,areas,distance_debug), mNofity.Notification_text_builder(true,areas,distance_debug));
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
        WakeLock wakelock = ((PowerManager) getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Illumino Service");
        wakelock.acquire();

        // get services
        am = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        settings = (SharedPreferences) getSharedPreferences(MainActivity.PREFS_NAME, 0);

        mShutDown = false;
        mContext = this;

        mHandler = new Handler();
        mDebug = new s_debug(mContext);
        mWakeup = new s_wakeup(mContext,(AlarmManager) getSystemService(Context.ALARM_SERVICE),mDebug);
        mNofity = new s_notify(mContext,settings);
        mNofity.setupNotifications((NotificationManager) getSystemService(NOTIFICATION_SERVICE));

        mDebug.write_to_file("this is on start");

//        if(mAlarmManager==null) {
//            mAlarmManager = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
//            mDebug.write_to_file("alarm manager stated");
//        } else {
//            mDebug.write_to_file("alarm manager was started");
//        }

        // establish comm interface
        registerReceiver(app_receiver, new IntentFilter(bg_service.SENDER));
        registerReceiver(network_change_receiver, new IntentFilter(android.net.ConnectivityManager.CONNECTIVITY_ACTION));

        // Register the listener with the Location Manager to receive location updates
        mLocationManager = (LocationManager) this.getSystemService(Context.LOCATION_SERVICE);
        if(!mLocationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)){
            Toast.makeText(getApplicationContext(), (String)"carolin debug: aaahh network provier is not on!", Toast.LENGTH_LONG).show();
            mDebug.write_to_file("carolin debug: aaahh network provier is not on!");
        }
        mLocationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 0, 0, locationListener);



        // start loop
        boolean recreate=false;
        mDebug.write_to_file("check if we should recreate");
        if(mWebSocketClient == null){
            recreate=true;
            mDebug.write_to_file("yes, or client is set to null");
        } else if(!mWebSocketClient.isConnected()) {
            recreate = true;
            mDebug.write_to_file("yes, is not connected");
        } else if(!mConnected){
            recreate = true;
            mDebug.write_to_file("yes, mConnected said so");
        }
        if(intent!=null) {
            if (s_wakeup.ACTION_CONNECT.equals(intent.getAction())) {
                recreate = true;
                mDebug.write_to_file("yes, this is ACTION CONNECT");
            } else if(s_wakeup.ACTION_PING.equals(intent.getAction())){
                mDebug.write_to_file("this is ACTION PING");
            }
        } else {
            mDebug.write_to_file("this is NO ACTION");
        }

        try {
            if (recreate) {
                mNofity.showNotification("Illumino", "connecting..", "");
                mDebug.write_to_file("not connected, try to reconnect");
                createWebSocket(); // create a new websockets, reuse is forbidden
            } else {
                mDebug.write_to_file("connection seams to be fine");
            }
        } catch (Exception ex){
            mDebug.write_to_file("exeption on connect:" + ex.toString());
        }

        if(mConnected && intent!=null){
            if(s_wakeup.ACTION_PING.equals(intent.getAction())){
                if(mWebSocketClient!=null && mWebSocketClient.isConnected()) {
                    JSONObject object = new JSONObject();
                    try {
                        object.put("cmd", "hb");
                    } catch (JSONException e) {
                        mDebug.write_to_file("exeption on put hb to JSON");
                        e.printStackTrace();
                    }
                    send_msg(object.toString());
                    last_ts_out=System.currentTimeMillis();
                }
            }
        }

        // just check if there is a timer, waiting for us or install one if there is none
        if(intent == null || (intent.getAction()==null) || (intent.getAction()!=null && !intent.getAction().equals(s_wakeup.ACTION_SHUT_DOWN)) ){
            if(!mWakeup.is_pinging(mContext)){
                mWakeup.start_pinging(mContext);
            } else {
                mDebug.write_to_file("There is a timer waiting for us");
            }
        }

        wakelock.release();
        return Service.START_STICKY;
    }


    @Override
    public IBinder onBind(Intent arg0) {
        return mBinder;
    }

    private BroadcastReceiver app_receiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            try {
                if (intent != null && intent.getExtras() != null) {

                    Bundle bundle = intent.getExtras();
                    if (bundle != null) {
                        String data = bundle.getString(bg_service.JSON, "");
                        if (!data.equals("")) {
                            send_msg(data);
                        }
                    }
                }
            }
            catch (Exception ex){
                mDebug.write_to_file("catched this on app_receiving " + ex.toString());
            }
        }
    };

    // this shall give us some infor if the network changes
    private BroadcastReceiver network_change_receiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            try {
                if (intent != null && intent.getExtras() != null) {
                    final ConnectivityManager connectivityManager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
                    final NetworkInfo ni = connectivityManager.getActiveNetworkInfo();

                    if (ni != null){
                        if(ni.isConnectedOrConnecting()) {
                            if (mNetworkType != null && !mNetworkType.equals(ni.getTypeName())) {
                                mDebug.write_to_file("Network was " + mNetworkType + " and changed to " + ni.getTypeName() + " calling restart ");
                                restart_connection();
                            }
                        }
                        mNetworkType=ni.getTypeName();
                    } else if (intent.getBooleanExtra(ConnectivityManager.EXTRA_NO_CONNECTIVITY, Boolean.FALSE)) {
                        mDebug.write_to_file("There's no network connectivity");
                        mNetworkType=""; // not null but resetet to empty
                    }
                }
            }
            catch (Exception ex){
                mDebug.write_to_file("catched this on network receiving " + ex.toString());
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
            mDebug.write_to_file("Setting up WebSocket and connecting");
            mWebSocketClient = new WebSocketConnection();
            mWebSocketClient.connect(wsuri, new WebSocketHandler() {
                // websocket is connected and has just opened
                @Override
                public void onOpen() {
                    mDebug.write_to_file("Socket Opened");
                    mConnected = true;
                    // on open -> login in.
                    JSONObject object = new JSONObject();
                    try {
                        object.put("cmd", "prelogin");
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                    mDebug.write_to_file("sending as socket is open: " + object.toString());
                    msg_out.clear();
                    send_msg(object.toString());
                }

                // websocket is connected and we've just received a message
                @Override
                public void onTextMessage(String message) {
                    mDebug.write_to_file("onMessage: " + message);

                    read_msg(message);
                }

                @Override
                public void onClose(int code, String reason) {
                    mDebug.write_to_file("On Closed " + reason);
                    restart_connection();
                }
            });
        }

        catch (WebSocketException e){
            mDebug.write_to_file("On Error " + e.getMessage());
            restart_connection();
        }
    }

    // restart
    private void restart_connection(){
        mWebSocketClient=null;
        mConnected = false;
        mLoggedIn = false;
        server_told_location = -1;
        mNofity.showNotification("Illumino", "disconnected", "");

        mWakeup.stop_pinging(mContext);

        mHandler.removeCallbacks(mWakeup.delayed_reconnect);
        mHandler.postDelayed(mWakeup.delayed_reconnect,5000); // start in 5 sec
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
                mDebug.write_to_file("received prelogin, sending " + o_snd.toString());
                //console.log(JSON.stringify(cmd_data));
                send_msg(o_snd.toString());
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // if we receive a login answer, we should check if we can answer with a location
            else if (cmd.equals("login")) {
                if (o_recv.getString("ok").equals("1")) {
                    mDebug.write_to_file("We are logged in!");
                    mLoggedIn = true;

                    // assuming we reconnected as a reaction on a server reboot, the server has no idea where we are. we should tell him right away if we know it
                    if (last_known_location.isValid()) {
                        mDebug.write_to_file("i have a valid location");
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
                            //mDebug.write_to_file("state:" + String.valueOf(o_recv.getInt("state")) + " " + String.valueOf(o_recv.getInt("detection")));
                            if (o_recv.getInt("state") == 1 && o_recv.getInt("detection") >= 1) {
                                if (am.getRingerMode() != AudioManager.RINGER_MODE_SILENT) {
                                    v.vibrate(500);
                                }
                                mNofity.set_area(o_recv.getString("area"));
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
                mNofity.showNotification("Illumino read message", mNofity.Notification_text_builder(false,areas,distance_debug), mNofity.Notification_text_builder(true, areas, distance_debug));
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // receive a image
            else if (cmd.equals("rf")) {
                byte[] decodedString = Base64.decode(o_recv.getString("img"), Base64.NO_OPTIONS);
                mNofity.set_image(BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length)); // todo: we need a kind of, if app has started reset picture to null
                mNofity.set_time();
                // show notification
                mNofity.showNotification("Illumino read file", mNofity.Notification_text_builder(false, areas, distance_debug), "");
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
            mDebug.write_to_file("Error on decoding incoming message " + e.getMessage());
        }
        wakelock.release();
    }

    // send a message or put it in the buffer
    private void send_msg(String input) {
        // check if we are dis-connected
        //mDebug.write_to_file("on send");
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


                mDebug.write_to_file("I don't think we are still connected, as " + s);
                restart_connection();
            }
        }catch (Exception ex){
            mDebug.write_to_file("Exception on check if client is connected in send_msg!! " + ex.toString());
        }


        // if we are still connected: send
        if(mConnected){
            ArrayList<Integer> msg_send = new ArrayList<Integer>();
            //mDebug.write_to_file("ich bin verbunden und habe "+String.valueOf(msg_out.size())+" Nachrichten.");

            for(int i=0;i<msg_out.size();i++) {
                //mDebug.write_to_file("Nachricht "+String.valueOf(i)+".");
                boolean send_this = false;
                if (mLoggedIn) {
                    //mDebug.write_to_file("Bin eingeloggt");
                    send_this = true;
                } else {
                    //mDebug.write_to_file("Bin nicht eingeloggt");
                    if (msg_out.get(i).indexOf("login") > 0) {
                        send_this = true;
                        //mDebug.write_to_file("Dafür hats was mit login zutun");
                    }
                }

                if (send_this){
                    //mDebug.write_to_file("Versuche zu senden");
                    try {
                        //mDebug.write_to_file("on send websocket");
                        mWebSocketClient.sendTextMessage(msg_out.get(i));
                        msg_send.add(i);
                    } catch (Exception ex) {
                        //mDebug.write_to_file("Exception on send -->" + ex.toString());
                        restart_connection();
                    }
                }
            }

            //mDebug.write_to_file("Entferne jetzt "+String.valueOf(msg_send.size())+" Nachrichten");
            // remove reverse ordered
            for(int i=msg_send.size()-1;i>=0;i--){
                int element=msg_send.get(i);
                msg_out.remove(element);
            }
            //mDebug.write_to_file("Hab noch "+String.valueOf(msg_out.size())+" Nachrichten");
        }
    }
    ///////////////////////////////////////////////////////////////////////////////
    ///////////////////////////// web socket handling /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
}