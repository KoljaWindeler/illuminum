package com.illumino.android_webapp;

import android.app.AlarmManager;
import android.app.NotificationManager;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.PowerManager;
import android.os.PowerManager.WakeLock;
import android.widget.Toast;
import org.json.JSONException;
import org.json.JSONObject;
import java.util.ArrayList;

public class bg_service extends Service {
    public static final String LOG = "LOG";
    public static final String SENDER = "BG_SENDER";


    private IBinder mBinder;
    private SharedPreferences mSettings = null;
    private LocationManager mLocationManager = null;
    private s_notify mNofity = null;
    private s_wakeup mWakeup = null;
    private s_debug mDebug = null;
    private s_ws mWs = null;
    private String mNetworkType = null;


    // debugging
    private String distance_debug = "";
    private s_coordinate last_known_location = new s_coordinate();
    private int server_told_location = -2;
    private Context mContext;


    ///////////////////////////////////////////////////////////////////////////////
    ////////////////////////////// location gedönese //////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
    public s_coordinate get_last_known_location() {
        return last_known_location;
    }

    // this is callen by the android service handle. When ever our location changes,
    // we are checking if we are IN a critical range of one of our known areas
    // if so, we check if that is still the same location that we've told the server
    // if now, we'll update the server
    public void check_locations(Location location) {
        last_known_location.setCoordinaes(location);
        int closest_area = -1;

        // debug
        distance_debug = "Distance Debug\n";

        // find closest s_area to our coordinates
        ArrayList<s_area> areas = mWs.get_areas();
        for (int i = 0; i < areas.size(); i++) {
            float this_distance = areas.get(i).getCoordinates().distanceTo(last_known_location.getCoordinaes());

            // debug
            distance_debug += "Area:" + areas.get(i).getName() + ", " + String.valueOf(this_distance) + "m\n";

            // check if we are IN a region
            if (this_distance < areas.get(i).getCriticalRange()) {
                // lets see if we are even closer to the coordinates then the others
                if (closest_area == -1) {
                    closest_area = i;
                } else { // so we had already a "close s_area"
                    // see if we are even closer to this one
                    if (this_distance < areas.get(closest_area).getCoordinates().distanceTo(last_known_location.getCoordinaes())) {
                        closest_area = i;
                    }
                }
            }
        }

        // only send an update if we are logged in
        if (mWs.mConnected && mWs.mLoggedIn) {
            // check if we should update the server
            if (server_told_location != closest_area) {
                server_told_location = closest_area;

                // tell the server that we are in that s_area
                JSONObject object = new JSONObject();
                try {
                    object.put("cmd", "update_location");
                    if (closest_area == -1) {
                        object.put("loc", "www");
                    } else {
                        object.put("loc", areas.get(closest_area).getName());
                    }

                    mDebug.write_to_file("Sending a location update to the server:"+object.toString());
                    //Log.i(getString(R.string.debug_id), object.toString());
                    //console.log(JSON.stringify(cmd_data));
                    mWs.send_msg(object.toString());

                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }

            // update once we've change our position, just for the DUBUG line!!
            mNofity.showNotification(getString(R.string.app_name)+" check location", mNofity.Notification_text_builder(false, areas), mNofity.Notification_text_builder(true, areas));
        }
    };

    // this will be called by the reconnect handle. this will enforce us to resend our current location
    public void resetLocation(){
        server_told_location=-1;
    }

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

    public String getDistanceDebug() {
        return distance_debug;
    }
    ///////////////////////////////////////////////////////////////////////////////
    ////////////////////////////// location gedönese //////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////////
    /////////////////////////////// android app stuff /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
    // https://github.com/schwiz/android-websocket-example/blob/master/src/net/schwiz/eecs780/PushService.java
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // aquire wakelock to run the complete onStartCommand routine without beeing interrupted
        WakeLock wakelock = ((PowerManager) getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, getString(R.string.app_name)+" Service");
        wakelock.acquire();

        mContext = this;

        if (mDebug == null) {
            mDebug = new s_debug(mContext);
        }

        // get services
        mDebug.write_to_file("settings check");
        if (mSettings == null) {
            mDebug.write_to_file("settings are null, recrating");
            mSettings = (SharedPreferences) getSharedPreferences(MainActivity.PREFS_NAME, MODE_MULTI_PROCESS);
            mDebug.write_to_file("settings pw is: "+mSettings.getString("PW","backup"));
        }
        mDebug.write_to_file("settings EOF");


        if (mWakeup == null) {
            mWakeup = new s_wakeup(mContext, (AlarmManager) getSystemService(Context.ALARM_SERVICE), mDebug);
        }

        if (mNofity == null) {
            mNofity = new s_notify(mContext, mSettings);
            mNofity.setupNotifications((NotificationManager) getSystemService(NOTIFICATION_SERVICE));
        }

        mDebug.write_to_file("==== This is on start ====");

        // establish comm interfaces to the APP and the NETWORK
        registerReceiver(network_change_receiver, new IntentFilter(ConnectivityManager.CONNECTIVITY_ACTION));

        // Register the listener with the Location Manager to receive location updates
        if (mLocationManager == null) {
            mLocationManager = (LocationManager) this.getSystemService(Context.LOCATION_SERVICE);
            if (!mLocationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                String danger = "Danger Danger, network provier is not on ... but I got no clue what to do!";
                Toast.makeText(getApplicationContext(), danger, Toast.LENGTH_LONG).show();
                mDebug.write_to_file(danger);
            }
            mLocationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 0, 0, locationListener);
        }

        /////////////////////////////////////////////////////////////////////////////////////////////////////
        ////////////////////////////////// WEBSOCKET KRAMS /////////////////////////////////////////////////
        /////////////////////////////////////////////////////////////////////////////////////////////////////
        // now we are getting serious .. start the websocket connection if it doesn't exist
        if (mWs == null) {
            // if this is the first start, create the object and link all the helper in
            mDebug.write_to_file("bg_serivce: create a new sharedPrefereces");
            mWs = new s_ws(mContext, mDebug, mNofity, mWakeup, mSettings);
        }

        /////// DEBUG //////////////
        mDebug.write_to_file("bg_service, onstart: check if we should recreate the WS");
        if (mWs.mWebSocketClient == null) {
            mDebug.write_to_file("yes, our mWebSocketClient is set to null");
        } else if (!mWs.mWebSocketClient.isConnected()) {
            mDebug.write_to_file("yes, is not connected");
        } else if (!mWs.mConnected) {
            mDebug.write_to_file("yes, mConnected said so");
        }
        /////// DEBUG //////////////

        // sanitary connection Checks
        boolean recreate = false;
        if (mWs.mWebSocketClient == null || !mWs.mWebSocketClient.isConnected() || !mWs.mConnected) {
            recreate = true;
        }
        // are we started with a JOB?
        // ACTION_CONNECT -> reconnect
        // ACTION_CHECK_PING -> check if we have received the ping ok, if not -> reconnect
        if (intent != null) {
            if (s_wakeup.ACTION_CONNECT.equals(intent.getAction())) { // that tells us that "disconenct" was called before this restart, so we have to reconnet
                recreate = true;
                mDebug.write_to_file("yes, this is ACTION CONNECT");
            } else if (s_wakeup.ACTION_CHECK_PING.equals(intent.getAction())) { // that tells us that "disconenct" was called before this restart, so we have to reconnet
                mDebug.write_to_file("This is a ping check");
                if(mWs.check_ping_received()==false) {
                    recreate = true;
                    mDebug.write_to_file("yes, we haven't received the ping ok from the server");
                }
            }
        }

        // execute the reconnect NOW
        if (recreate) {
            try {
                mNofity.showNotification(getString(R.string.app_name), "connecting..", "");
                mDebug.write_to_file("bg_service, onstart: state is 'not connected', try to reconnect");
                mWs.createWebSocket(); // create and connected to a new websockets, reuse is forbidden
            } catch (Exception ex) {
                mDebug.write_to_file("exeption on connect:" + ex.toString());
            }
        } else {
            mDebug.write_to_file("WS connection seams to be fine");
            // if we are connected .. or at least we think so .. try to ping if thats why we started
            if (intent!=null && s_wakeup.ACTION_PING.equals(intent.getAction())) {
                JSONObject object = new JSONObject();
                try {
                    object.put("cmd", "ws_hb");
                } catch (JSONException e) {
                    mDebug.write_to_file("exeption on put hb to JSON");
                    e.printStackTrace();
                }
                mDebug.write_to_file("This is a PING intent, fireing a ping to the server!");
                mDebug.write_to_file("Websocket: send: " + object.toString());
                mWs.send_msg(object.toString()); // send ws_hb
                mWakeup.start_ping_check(this); // schedule check in 60 sec
                mWs.last_ts_out = System.currentTimeMillis();
            }
        }
        /////////////////////////////////////////////////////////////////////////////////////////////////////
        ////////////////////////////////// WEBSOCKET KRAMS /////////////////////////////////////////////////
        /////////////////////////////////////////////////////////////////////////////////////////////////////

        ////////////////////////////////////////////////////////////////////////////////////////////
        ////////////////////////////////// WAKE UP /////////////////////////////////////////////////
        ////////////////////////////////////////////////////////////////////////////////////////////
        // just check if there is a timer, waiting for us or install one if there is none
        if (intent == null || (intent.getAction() == null) || (intent.getAction() != null && !intent.getAction().equals(s_wakeup.ACTION_SHUT_DOWN))) {
            if (!mWakeup.is_pinging(mContext)) {
                mWakeup.start_pinging(mContext);
            } else {
                mDebug.write_to_file("bg_service, OnStartCommand: There is a ping-timer-intent waiting for us, no need to create a new one.");
            }
        }
        ////////////////////////////////////////////////////////////////////////////////////////////
        ////////////////////////////////// WAKE UP /////////////////////////////////////////////////
        ////////////////////////////////////////////////////////////////////////////////////////////

        mDebug.write_to_file("==== on start DONE ====");
        wakelock.release();
        return Service.START_STICKY;
    }


    @Override
    public IBinder onBind(Intent arg0) {
        return mBinder;
    }

        // this shall give us some information if the network changes
    private BroadcastReceiver network_change_receiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            try {
                if (intent != null && intent.getExtras() != null) {
                    final ConnectivityManager connectivityManager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
                    final NetworkInfo ni = connectivityManager.getActiveNetworkInfo();

                    if (ni != null) {
                        if (ni.isConnectedOrConnecting()) {
                            // if connection is different now than it was last time -> reconnect
                            if (mNetworkType != null && !mNetworkType.equals(ni.getTypeName())) {
                                mDebug.write_to_file("Network was " + mNetworkType + " and changed to " + ni.getTypeName() + " calling restart ");
                                mWs.restart_connection();
                            }
                        }
                        // save every time, even if the type is "". This will result in a reconnect if we've lost the connection in between. Mobile -> "" -> Mobile
                        mNetworkType = ni.getTypeName();
                    } else if (intent.getBooleanExtra(ConnectivityManager.EXTRA_NO_CONNECTIVITY, Boolean.FALSE)) {
                        mDebug.write_to_file("There's no network connectivity");
                        mNetworkType = ""; // not null but resetet to empty
                    }
                }
            } catch (Exception ex) {
                mDebug.write_to_file("catched this on network receiving " + ex.toString());
            }
        }
    };
    ///////////////////////////////////////////////////////////////////////////////
    /////////////////////////////// android app stuff /////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////
}