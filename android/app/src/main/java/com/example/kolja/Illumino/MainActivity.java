package com.example.kolja.Illumino;

import android.content.SharedPreferences;
import android.location.Location;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.app.Activity;
import android.util.Log;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;
import android.content.BroadcastReceiver;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;

import org.java_websocket.util.Base64;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Vector;

import android.widget.ListView;



public class MainActivity extends Activity implements android.view.View.OnClickListener {
    public static final String PREFS_NAME = "IlluminoSettings";
    ArrayList<ListContainer> res_data = new ArrayList<ListContainer>();
    SharedPreferences settings;
    private s_debug mDebug = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Intent intent = new Intent(this, bg_service.class);
        startService(intent);

        // set message that we need an update
        try {
            JSONObject o_snd = new JSONObject();
            o_snd.put("cmd", "refresh_ws");
            Intent send_intent = new Intent(bg_service.SENDER);
            send_intent.putExtra(s_ws.TYPE,s_ws.APP2SERVER);
            send_intent.putExtra(s_ws.PAYLOAD,o_snd.toString());
            sendBroadcast(send_intent);
        } catch (Exception e) {

        }


        settings = getSharedPreferences(PREFS_NAME, 0);
        String login =settings.getString("LOGIN","Kolja");
        ((Button)findViewById(R.id.save_id)).setOnClickListener(this);
        ((EditText)findViewById(R.id.id)).setText(login);
        if (mDebug == null) {
            mDebug = new s_debug(this);
        }

    }

    @Override
    public void onClick(View arg0) {
        switch (arg0.getId()) {
            case R.id.save_id:
                String login=((EditText)findViewById(R.id.id)).getText().toString();
                SharedPreferences.Editor editor = settings.edit();
                editor.putString("LOGIN", login);
                editor.commit();
                // restart service
                Intent intent = new Intent(this, bg_service.class);
                stopService(intent);
                startService(intent);
                break;
        }
    };

    @Override
    protected void onResume() {
        super.onResume();
        registerReceiver(receiver, new IntentFilter(s_ws.NOTIFICATION));
    }
    @Override
    protected void onPause() {
        super.onPause();
        unregisterReceiver(receiver);
    }

    private BroadcastReceiver receiver = new BroadcastReceiver() {

        @Override
        public void onReceive(Context context, Intent intent) {
            Bundle bundle = intent.getExtras();
            if (bundle != null) {
                if(bundle.containsKey(s_ws.TYPE) && bundle.containsKey(s_ws.PAYLOAD)) {
                    String type = bundle.getString(s_ws.TYPE,"");
                    String data = bundle.getString(s_ws.PAYLOAD,"");
                    String cmd;
                    String mid="";

                    JSONObject object = new JSONObject();

                    try {
                        object = new JSONObject(data);
                        cmd = object.getString("cmd");
                        mid=object.getString("mid");
                    } catch (Exception e) {
                        cmd = "";
                    }
                    int id = mid2id(mid);
                    ListView WebcamView = (ListView) findViewById(R.id.listScroller);


                    if (cmd.equals("rf")) {
                        try {
                            Long tsLong = System.currentTimeMillis();
                            if (id > -1) {
                                // decode it
                                String encodedImage = object.getString("img");
                                byte[] decodedString = Base64.decode(encodedImage, Base64.NO_OPTIONS);
                                Bitmap decodedByte = BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length);

                                // save it
                                res_data.get(id).last_img=decodedByte;

                                // display it or not?
                                if(id>=WebcamView.getFirstVisiblePosition() && id<=WebcamView.getLastVisiblePosition()) {

                                    int pos = id - WebcamView.getFirstVisiblePosition();
                                    View v = WebcamView.getChildAt(pos);

                                    // is this a alert picture, it has movement and detection, both flagged as on
                                    if(Integer.parseInt(object.getString("state"))>0 && Integer.parseInt(object.getString("detection"))>0) {
                                        // if this is a alert, then the picture is not open. there for we have to open it
                                        if(!((ListAdapter)WebcamView.getAdapter()).isPicOpen(id)){
                                            ((ListAdapter) WebcamView.getAdapter()).showPic(id);
                                        }
                                    }

                                    ImageView webcam_pic;
                                    webcam_pic = (ImageView) v.findViewById(R.id.webcam_pic);
                                    webcam_pic.setImageBitmap(decodedByte);
                                }
                            }

                            //((ImageView)findViewById(R.id.Foto)).setImageBitmap(decodedByte);
                            Log.i("websocket", "bitmap set");

                            Long tsLong2 = System.currentTimeMillis() - tsLong;
                            String ts = tsLong2.toString();
                            //textView.setText(textView.getText() + "\n" + ts);

                        } catch (Exception e) {
                            int ignore = 0;
                        }
                    } else if (cmd.equals("m2v_login")) {
                        try {
                            // add an object that will hold the ID "mid", "s_area","state","account"
                            if(id==-1) { // MID not known
                                String area = object.getString("area");
                                String alias = object.getString("alias");
                                int state = object.getInt("state");
                                int detection = object.getInt("detection");
                                int last_seen = object.getInt("last_seen");
                                Location new_loc = new Location("new");
                                if (!object.getString("latitude").equals("") && !object.getString("longitude").equals("")) {
                                    new_loc.setLatitude(Float.parseFloat(object.getString("latitude")));
                                    new_loc.setLongitude(Float.parseFloat(object.getString("longitude")));
                                } else {
                                    new_loc.setLatitude(0.0);
                                    new_loc.setLongitude(0.0);
                                }

                                prepare_adapter(mid, state, area, detection, new_loc, last_seen, alias);
                            }

                        } catch (Exception e) {
                            int ignore = 0;
                        }
                    }

                    else if(cmd.equals("state_change")){
                        if(id>-1){
                            try {
                                res_data.get(id).state = Integer.parseInt(object.getString("state"));
                                ((ListAdapter)WebcamView.getAdapter()).setState(id);
                            } catch(Exception ex){

                            }
                        }
                    }

                    else if(cmd.equals("hb")){
                        if(id>-1){
                            try {
                                float intermediat=Float.parseFloat(object.getString("ts"));
                                res_data.get(id).last_seen = (long)intermediat;
                                ((ListAdapter)WebcamView.getAdapter()).setUpdated(id);
                            } catch(Exception ex){

                            }
                        }
                    }
                }

            }
        }
    };

    private int mid2id(String mid) {
        int id = -1;
        for (int i = 0; i < res_data.size(); i++) {
            if (res_data.get(i).mid.equals(mid)) {
                id = i;
            }
        }
        return id;
    }

    private void prepare_adapter(String mid, int state, String area, int detection, Location l, int last_seen, String alias){
        ListView liste = (ListView)findViewById(R.id.listScroller);
        if(liste!=null){
            res_data.add(new ListContainer(mid, state, area, detection, l, last_seen, alias));

            ListAdapter adapter = new ListAdapter(this,R.layout.listentry,res_data.toArray(new ListContainer[res_data.size()]));
            liste.setAdapter(adapter);
        }
    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }



}
