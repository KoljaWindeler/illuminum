package com.example.kolja.Illumino;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.BitmapFactory;
import android.location.Location;
import android.media.AudioManager;
import android.os.Handler;
import android.os.PowerManager;
import android.os.Vibrator;
import android.telephony.TelephonyManager;

import org.java_websocket.util.Base64;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;

import de.tavendo.autobahn.WebSocketConnection;
import de.tavendo.autobahn.WebSocketException;
import de.tavendo.autobahn.WebSocketHandler;

public class s_ws {
    //public static final String JSON = "JSON";
    public static final String TYPE = "TYPE";
    public static final String PAYLOAD = "PAYLOAD";
    public static final String APP2SERVER = "APP2SERVER";
    public static final String APP2SERVICE = "APP2SERVICE";
    public static final String SERVICE2APP = "SERVICE2APP";
    public static final String SERVER2APP = "SERVER2APP";
    public static final String NOTIFICATION = "BG_RECEIVER";


    private final Context mContext;
    private final s_debug mDebug;
    private final s_notify mNofity;
    private final s_wakeup mWakeup;
    private Handler mHandler;
    private SharedPreferences settings;
    private AudioManager am;
    private Vibrator v;

    private ArrayList<s_area> areas = new ArrayList<s_area>();
    private long last_ts_in;
    public long last_ts_out;
    public WebSocketConnection mWebSocketClient;
    public boolean mConnected;
    public boolean mLoggedIn;



    private ArrayList<String> msg_out = new ArrayList<String>();

    public s_ws(Context ServiceContext, s_debug ServiceDebug, s_notify ServiceNofity, s_wakeup ServiceWakeup, SharedPreferences ServiceSettings) {
        mContext = ServiceContext;
        mDebug = ServiceDebug;
        mNofity = ServiceNofity;
        mWakeup = ServiceWakeup;
        mHandler = new Handler();
        settings = ServiceSettings;
        am = (AudioManager) mContext.getSystemService(mContext.AUDIO_SERVICE);
        v = (Vibrator) mContext.getSystemService(mContext.VIBRATOR_SERVICE);
        areas.clear();
    }


    public void createWebSocket() {

        final String wsuri = "ws://172.12.213.117:10820";

        try {
            last_ts_in=0;
            mDebug.write_to_file("Websocket: Setting up WebSocket and connecting");
            mWebSocketClient = new WebSocketConnection();
            mWebSocketClient.connect(wsuri, new WebSocketHandler() {
                // websocket is connected and has just opened
                @Override
                public void onOpen() {
                    mDebug.write_to_file("Websocket: Socket Opened");
                    mConnected = true;
                    // on open -> login in.
                    JSONObject object = new JSONObject();
                    try {
                        object.put("cmd", "prelogin");
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                    mDebug.write_to_file("Websocket: sending as socket is open: " + object.toString());
                    msg_out.clear();
                    send_msg(object.toString());
                }

                // websocket is connected and we've just received a message
                @Override
                public void onTextMessage(String message) {
                    read_msg(message);
                }

                @Override
                public void onClose(int code, String reason) {
                    mDebug.write_to_file("Websocket: On Closed " + reason);
                    restart_connection();
                }
            });
        }

        catch (WebSocketException e){
            mDebug.write_to_file("Websocket: On Error " + e.getMessage());
            restart_connection();
        }
    }

    // restart
    public void restart_connection(){
        mDebug.write_to_file("Websocket: -= This is restart connection =-");
        mWebSocketClient=null;
        mConnected = false;
        mLoggedIn = false;
        ((bg_service)mContext).resetLocation();
        mNofity.showNotification("Illumino", "disconnected", "");

        mWakeup.stop_pinging(mContext);

        mHandler.removeCallbacks(mWakeup.delayed_reconnect);
        mHandler.postDelayed(mWakeup.delayed_reconnect,5000); // start in 5 sec
    }


    // handle message that came in
    private void read_msg(String message){
        PowerManager.WakeLock wakelock = ((PowerManager)((bg_service)mContext).getSystemService(mContext.POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Illumino");
        wakelock.acquire();
        last_ts_in = System.currentTimeMillis();

        // forward message to possible listening apps
        Intent intent = new Intent(NOTIFICATION);
        intent.putExtra(TYPE, SERVER2APP);
        intent.putExtra(PAYLOAD, message);
        mContext.sendBroadcast(intent);

        // but check if we could use it
        String cmd;
        try {
            JSONObject o_recv = new JSONObject(message);
            JSONObject o_snd = new JSONObject();
            cmd = o_recv.getString("cmd");

            //////////////////////////////////////////////////////////////////////////////////////
            // if we receive a prelogin answer, we have to calc our login and send it to the server
            if (cmd.equals("prelogin")) {
                mDebug.write_to_file("Websocket: Received: " + message);
                try {
                    TelephonyManager tManager = (TelephonyManager)mContext.getSystemService(Context.TELEPHONY_SERVICE);
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
                mDebug.write_to_file("Websocket: received prelogin, sending " + o_snd.toString());
                //console.log(JSON.stringify(cmd_data));
                send_msg(o_snd.toString());
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // if we receive a login answer, we should check if we can answer with a location
            else if (cmd.equals("login")) {
                mDebug.write_to_file("Websocket: Received: " + message);
                if (o_recv.getString("ok").equals("1")) {
                    mDebug.write_to_file("Websocket: We are logged in!");
                    mLoggedIn = true;

                    // assuming we reconnected as a reaction on a server reboot, the server has no idea where we are. we should tell him right away if we know it
                    if ((((bg_service)mContext).get_last_known_location()).isValid()) {
                        mDebug.write_to_file("i have a valid location");
                        ((bg_service)mContext).check_locations((((bg_service)mContext).get_last_known_location()).getCoordinaes());
                    }


                    // check if we have messages in the q
                    send_msg("");
                }
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // update our list of areas
            else if (cmd.equals("m2v_login") || cmd.equals("detection_changed") || cmd.equals("state_change")) {
                mDebug.write_to_file("Websocket: Received: " + message);
                int found = 0;
                //mDebug.write_to_file("search for area in array, size:"+String.valueOf(areas.size()));
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
                    //mDebug.write_to_file("creating new area");
                    areas.add(new s_area(name, det, new_loc, 500, state));
                    //mDebug.write_to_file("Done");
                }

                // show notification
                mNofity.showNotification("Illumino read message", mNofity.Notification_text_builder(false,areas), mNofity.Notification_text_builder(true, areas));
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // receive a image
            else if (cmd.equals("rf")) {
                mDebug.write_to_file("Websocket: Received file");
                if(Integer.parseInt(o_recv.getString("state"))!=0) {
                    byte[] decodedString = Base64.decode(o_recv.getString("img"), Base64.NO_OPTIONS);
                    mNofity.set_image(BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length)); // todo: we need a kind of, if app has started reset picture to null
                    mNofity.set_time();
                    // show notification
                    mNofity.showNotification("Illumino read file", mNofity.Notification_text_builder(false, areas), "");
                }
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // receive a heartbeat answer
            //else if (cmd.equals("hb")){
            else if (cmd.equals("shb")) {
                mDebug.write_to_file("Websocket: Received: " + message);
                try {
                    o_snd.put("cmd", "shb");
                    o_snd.put("ok", 1);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
                //Log.i(getString(R.string.debug_id), o_snd.toString());
                //console.log(JSON.stringify(cmd_data));
                mDebug.write_to_file("Websocket: send: " + o_snd.toString());
                send_msg(o_snd.toString());
            }

            else {
                mDebug.write_to_file("Websocket: I got no idea why i've received this: " + message);
            }

        } catch (Exception e) {
            mDebug.write_to_file("Websocket: Error on decoding incoming message " + e.getMessage());
        }
        wakelock.release();
    }

    public ArrayList<s_area> get_areas(){
        return areas;
    }

    // send a message or put it in the buffer
    public void send_msg(String input) {
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


                mDebug.write_to_file("Websocket: I don't think we are still connected, as " + s);
                restart_connection();
            }
        }catch (Exception ex){
            mDebug.write_to_file("Websocket: Exception on check if client is connected in send_msg!! " + ex.toString());
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
                        //mDebug.write_to_file("Dafuer hats was mit login zutun");
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

//    public void broadcast_areas() {
//        try {
//            for(int i=0; i<areas.size(); i++) {
//                JSONObject o_snd = new JSONObject();
//                o_snd.put("cmd","m2v_login");
//                o_snd.put("cmd",areas.get(i).getName());
//
//                {"account": "jkw", "area": "baker", "cmd": "m2v_login", "mid": "202481600132415", "longitude": "-95.369136", "detection": 1, "alias": "livingroom rpi2b", "state": 0, "latitude": "29.968327", "last_seen": 1432058785.419504}
//
//                Intent intent = new Intent(NOTIFICATION);
//                intent.putExtra(TYPE, SERVICE2APP);
//                intent.putExtra(PAYLOAD, o_snd.toString());
//                mContext.sendBroadcast(intent);
//            }
//        } catch (Exception ex){
//
//        }
//    }
}
