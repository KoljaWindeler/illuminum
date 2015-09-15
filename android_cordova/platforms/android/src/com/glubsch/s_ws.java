package com.glubsch;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.BitmapFactory;
import android.location.Location;
import android.media.AudioManager;
import android.os.Handler;
import android.os.PowerManager;
import android.os.SystemClock;
import android.os.Vibrator;
import android.telephony.TelephonyManager;
import android.util.Base64;
import android.util.Log;


import org.json.JSONException;
import org.json.JSONObject;

import java.net.URI;
import java.security.MessageDigest;
import java.util.ArrayList;

import de.tavendo.autobahn.WebSocket.WebSocketConnectionObserver;
import de.tavendo.autobahn.WebSocketConnection;
import de.tavendo.autobahn.WebSocketException;

public class s_ws implements WebSocketConnectionObserver {
    //public static final String JSON = "JSON";
    public static final String CLEAR_ALARM = "CLEAR_ALARM";


    private final Context mContext;
    private final s_debug mDebug;
    private final s_notify mNofity;
    private final s_wakeup mWakeup;
    private Handler mHandler;
    private SharedPreferences settings;
    private AudioManager am;
    private Vibrator v;

    public ArrayList<s_area> areas = new ArrayList<s_area>();
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

        final String wsuri = "wss://52.24.157.229:9879";
        try {

            last_ts_in=0;
            mDebug.write_to_file("Websocket: Setting up WebSocket and connecting");
            mWebSocketClient = new WebSocketConnection();
            mWebSocketClient.connect(new URI(wsuri), this);
        }
        catch (Exception e){
            mDebug.write_to_file("Websocket: On Error " + e.getMessage());
            restart_connection();
        }
    }



    // WebSocket Handler callbacks
    @Override
    public void onOpen() {
        mConnected = true;
        mDebug.write_to_file("Websocket: Socket Opened");
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

    @Override
    public void onClose(WebSocketCloseNotification code, String reason) {
        mConnected = false;
        mDebug.write_to_file("Websocket: On Closed " + reason);
        restart_connection();
    }

    @Override
    public void onTextMessage(String message) {
        read_msg(message);
    }

    @Override
    public void onRawTextMessage(byte[] payload) {
    }

    @Override
    public void onBinaryMessage(byte[] payload) {
    }


    // restart
    public void restart_connection(){
        mDebug.write_to_file("Websocket: -= This is restart connection =-");
        mWebSocketClient=null;
        mConnected = false;
        mLoggedIn = false;
        ((bg_service)mContext).resetLocation();
        mNofity.showNotification(mContext.getString(R.string.app_name), "disconnected", "");

        mWakeup.stop_pinging(mContext);

        mHandler.removeCallbacks(mWakeup.delayed_reconnect);
        mHandler.postDelayed(mWakeup.delayed_reconnect, 5000); // start in 5 sec
    }


    private static String convertToHex(byte[] data) {
        StringBuilder buf = new StringBuilder();
        for (byte b : data) {
            int halfbyte = (b >>> 4) & 0x0F;
            int two_halfs = 0;
            do {
                buf.append((0 <= halfbyte) && (halfbyte <= 9) ? (char) ('0' + halfbyte) : (char) ('a' + (halfbyte - 10)));
                halfbyte = b & 0x0F;
            } while (two_halfs++ < 1);
        }
        return buf.toString();
    }

    // handle message that came in
    private void read_msg(String message){
        PowerManager.WakeLock wakelock = ((PowerManager)((bg_service)mContext).getSystemService(mContext.POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, mContext.getString(R.string.app_name));
        wakelock.acquire();
        last_ts_in = System.currentTimeMillis();

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
                String login=null;
                try {
                    TelephonyManager tManager = (TelephonyManager)mContext.getSystemService(Context.TELEPHONY_SERVICE);
                    String uuid = tManager.getDeviceId();

                    mDebug.write_to_file("s_ws: read from sharedPrefereces");
                    login = settings.getString("LOGIN", MainActivity.nongoodlogin);
                    String pw = settings.getString("PW", MainActivity.nongoodlogin);
                    //mDebug.write_to_file("s_ws: result " + pw);

                    // encrypt pw to hash
                    MessageDigest digester = MessageDigest.getInstance("MD5");
                    digester.update(pw.getBytes());
                    String digest = convertToHex(digester.digest());

                    //mDebug.write_to_file(pw+" as hash is "+digest);
                    // append the challange to the hash and hash again
                    String sec=digest+o_recv.getString("challange");

                    digester = MessageDigest.getInstance("MD5");
                    digester.update(sec.getBytes("UTF-8"));
                    digest = convertToHex(digester.digest());

                    //mDebug.write_to_file("together we have "+sec+" as hash is "+digest);
                    mDebug.write_to_file("Websocket: send login:" + login+ "/"+digest);
                    o_snd.put("cmd", "login");
                    o_snd.put("login", login);
                    o_snd.put("uuid", uuid);
                    o_snd.put("alarm_view",1);

                    o_snd.put("client_pw", digest);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
                //console.log(JSON.stringify(cmd_data));
                if(!login.equals(MainActivity.nongoodlogin)) {
                    send_msg(o_snd.toString());
                    mDebug.write_to_file("Websocket: received prelogin, sending " + o_snd.toString());
                } else {
                    mNofity.showNotification("Not logged in","","");
                }
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
                } else {
                    mDebug.write_to_file("Websocket: Damn, login rejected!");
                    mLoggedIn = false;
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
                        update_state_detection(o_recv);
                        break;
                    }
                }

                // first sign up .. add to list
                if (found == 0) {
                    String name = o_recv.getString("area");
                    Integer det = o_recv.getInt("detection");
                    Location new_loc = new Location("new");
                    String mid= o_recv.getString("mid");
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
                    areas.add(new s_area(name, det, new_loc, 500, state, mid));
                    //mDebug.write_to_file("Done");
                    ((bg_service) mContext).resetLocation();
                    ((bg_service) mContext).check_locations(((bg_service) mContext).get_last_known_location().getCoordinaes());
                }

                // show notification
                mNofity.showNotification(mContext.getString(R.string.app_name), mNofity.Notification_text_builder(false,areas), mNofity.Notification_text_builder(true, areas));
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // receive a image from the server
            else if (cmd.equals("rf")) {
                mDebug.write_to_file("Websocket: Received file");

                int state=Integer.parseInt(o_recv.getString("state"));
                int detection=Integer.parseInt(o_recv.getString("detection"));
                if(state!=0 && detection!=0) {
                    update_state_detection(o_recv);


                    byte[] decodedString = Base64.decode(o_recv.getString("img"),0);
                    mNofity.set_image(BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length)); // todo: we need a kind of, if app has started reset picture to null
                    mNofity.set_time();
                    // show notification
                    //mNofity.showNotification(mContext.getString(R.string.app_name)+" read file", mNofity.Notification_text_builder(false, areas), "");
                }
            }

            //////////////////////////////////////////////////////////////////////////////////////
            // receive a heartbeat answer
            else if (cmd.equals("ws_hb")){
                // this is just the "ok"
                // last_ts_in will be set by EVERY message
                mDebug.write_to_file("HB_return");
            }
//            else if (cmd.equals("shb")) {
//                mDebug.write_to_file("Websocket: Received: " + message);
//                try {
//                    o_snd.put("cmd", "shb");
//                    o_snd.put("ok", 1);
//                } catch (JSONException e) {
//                    e.printStackTrace();
//                }
//                //Log.i(getString(R.string.debug_id), o_snd.toString());
//                //console.log(JSON.stringify(cmd_data));
//                mDebug.write_to_file("Websocket: send: " + o_snd.toString());
//                send_msg(o_snd.toString());
//            }
            else {
                mDebug.write_to_file("Websocket: I got no idea why i've received this: " + message);
            }

        } catch (Exception e) {
            mDebug.write_to_file("Websocket: Error on decoding incoming message " + e.getMessage());
        }
        wakelock.release();
    }


    private void update_state_detection(JSONObject o_recv) {
        int state= -1;
        int detection= -1;
        String area ="";
        // try to get it
        try {
            state = Integer.parseInt(o_recv.getString("state"));
            detection = Integer.parseInt(o_recv.getString("detection"));
            area = o_recv.getString("area");
        } catch (JSONException e) {
            e.printStackTrace();
        }


        // if got state successful
        if(state!=-1 && detection!=-1 && !area.equals("")) {
            // just make sure that we have vibrated
            for (int i = 0; i < areas.size(); i++) {
                // find correct area
                if (areas.get(i).getName().equals(area)) {
                    // check if detection is not in sync
                    if (areas.get(i).getDetection() != detection || areas.get(i).getState() != state) {
                        // update and vibrate if needed
                        areas.get(i).setState(state);
                        areas.get(i).setDetection(detection);

                        if(detection>0 && state>0) {
                            mNofity.set_area(area); // set last alarm area
                            if (am.getRingerMode() != AudioManager.RINGER_MODE_SILENT) {
                                //v.vibrate(500);
                            }
                        }
                    }
                }
            }
        }
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

    // check if we have received the ping answer on time
    public boolean check_ping_received() {
        // if there was a ping out within the last 90 sec but no ping in after that .. bad .. return false
        mDebug.write_to_file("Ping check:"+String.valueOf(last_ts_out)+"+1000*90>"+String.valueOf(System.currentTimeMillis())+" vs "+String.valueOf(last_ts_in));

        if(last_ts_out+1000*90 > System.currentTimeMillis()){
            if(last_ts_out>last_ts_in){
                mDebug.write_to_file("problem");
                return false;
            }
            mDebug.write_to_file("No problem");
        }
        mDebug.write_to_file("No ping send within the last 60 sec");
        return true;
    }
}
