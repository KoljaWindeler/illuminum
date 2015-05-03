package com.example.kolja.alert_app;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;

import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.util.Log;

import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.json.JSONException;
import org.json.JSONObject;
import android.os.Bundle;
import android.content.Context;
import android.content.BroadcastReceiver;
import android.content.IntentFilter;

public class bg_service extends Service {
    public static final java.lang.String LOG = "LOG";
    public static final java.lang.String JSON = "JSON";
    IBinder mBinder;
    private ArrayList<String> list = new ArrayList<String>();
    public static final String NOTIFICATION = "alert_bg_receiver";
    public static final String SENDER = "alert_bg_sender";
    private WebSocketClient mWebSocketClient;
    LocationManager locationManager;
    private int loc_home =-1;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {

        connectWebSocket();
        registerReceiver(receiver, new IntentFilter(bg_service.SENDER));
        // Register the listener with the Location Manager to receive location updates
        locationManager= (LocationManager) this.getSystemService(Context.LOCATION_SERVICE);
        locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 0, 0, locationListener);


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
            } else if(loc_home !=1) {
                object.put("loc", "home"); // 0 off
                loc_home = 1;
                fire=1;
            }

           if(fire==1) {
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
        public void onLocationChanged(Location location) {
            // Called when a new location is found by the network location provider.
            check_locations(location);

        }

        public void onStatusChanged(String provider, int status, Bundle extras) {}

        public void onProviderEnabled(String provider) {}

        public void onProviderDisabled(String provider) {}
    };



    private void connectWebSocket() {
        URI uri;
        try {
            uri = new URI("ws://192.168.1.80:9876");
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

            }

            @Override
            public void onMessage(String message) {
                //TextView textView = (TextView)findViewById(R.id.log);
                //textView.setText(textView.getText() + "\n" + message);
                Log.i("Websocket", "onMessage ");
                String cmd;
                JSONObject object = new JSONObject();

                try {
                    object = new JSONObject(message);
                    cmd=object.getString("cmd");
                } catch (Exception e) {
                    cmd="";
                }

                if(cmd.equals("test")) {
                    int ignore=1;
                } else if(!cmd.equals("")){ // if not empty
                    Intent intent = new Intent(NOTIFICATION);
                    intent.putExtra(JSON, message);
                    sendBroadcast(intent);
                }
            }

            @Override
            public void onClose(int i, String s, boolean b) {
                Log.i("Websocket", "Closed " + s);
                Log.i("Websocket", "Reconnecting ");
                connect();
            }

            @Override
            public void onError(Exception e) {
                Log.i("Websocket", "Error " + e.getMessage());
            }
        };
        mWebSocketClient.connect();
    }

}