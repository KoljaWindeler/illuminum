package com.example.kolja.Illumino;

import android.content.SharedPreferences;
import android.location.Location;
import android.os.Bundle;
import android.util.SparseArray;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuItem;
import android.app.Activity;
import android.util.Log;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseExpandableListAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ExpandableListView;
import android.widget.ImageView;
import android.content.BroadcastReceiver;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;

import org.java_websocket.util.Base64;
import org.json.JSONObject;

import java.util.ArrayList;

import android.widget.ListView;
import android.widget.TextView;


public class MainActivity extends Activity implements android.view.View.OnClickListener {
    public static final String PREFS_NAME = "IlluminoSettings";
    SharedPreferences settings;
    private s_debug mDebug = null;
    SparseArray<areas> data = new SparseArray<areas>();
    private ListAdapter mAdapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        View view = View.inflate(this, R.layout.expendable_header, null);
        ExpandableListView liste = (ExpandableListView)findViewById(R.id.listScroller);
        liste.addHeaderView(view, null, false);

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


        /*settings = getSharedPreferences(PREFS_NAME, 0);
        String login =settings.getString("LOGIN","Kolja");
        ((Button)findViewById(R.id.save_id)).setOnClickListener(this);
        ((EditText)findViewById(R.id.id)).setText(login);
        */

        if (mDebug == null) {
            mDebug = new s_debug(this);
        }

    }

    @Override
    public void onClick(View arg0) {
        switch (arg0.getId()) {
            /*case R.id.save_id:
                String login=((EditText)findViewById(R.id.id)).getText().toString();
                SharedPreferences.Editor editor = settings.edit();
                editor.putString("LOGIN", login);
                editor.commit();
                // restart service
                Intent intent = new Intent(this, bg_service.class);
                stopService(intent);
                startService(intent);
                break;*/
        }
    };

    @Override
    protected void onResume() {
        super.onResume();
        registerReceiver(receiver, new IntentFilter(s_ws.NOTIFICATION));
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
                    String payload = bundle.getString(s_ws.PAYLOAD,"");
                    String cmd;
                    String mid="";

                    JSONObject object = new JSONObject();

                    try {
                        object = new JSONObject(payload);
                        cmd = object.getString("cmd");
                        if(object.has("mid")) {
                            mid = object.getString("mid");
                        }
                    } catch (Exception e) {
                        cmd = "";
                    }
                    int id[] = mid2id(mid);
                    ExpandableListView WebcamView = (ExpandableListView) findViewById(R.id.listScroller);


                    if (cmd.equals("rf")) {
                        try {
                            Long tsLong = System.currentTimeMillis();
                            if (id[0] > -1) {
                                // decode it
                                String encodedImage = object.getString("img");
                                byte[] decodedString = Base64.decode(encodedImage, Base64.NO_OPTIONS);
                                Bitmap decodedByte = BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length);

                                // save it
                                data.get(id[0]).m2mList.get(id[1]).last_img = decodedByte;
                                //mAdapter.showpic(id[0],id[1]);


                                // display it or not?
                                View v = getView_ifVisible(id[0], id[1], WebcamView);
                                if (v != null) {
                                    // is this a alert picture, it has movement and detection, both flagged as on
                                    if (Integer.parseInt(object.getString("state")) > 0 && Integer.parseInt(object.getString("detection")) > 0) {
                                        // if this is a alert, then the picture is not open. there for we have to open it
                                        if (!((ListAdapter) WebcamView.getAdapter()).isPicOpen(id[0], id[1])) {
                                            ((ListAdapter) WebcamView.getAdapter()).showPic(v, id[0], id[1]);
                                        }
                                    }
                                    View v2 = ((ViewGroup) v.findViewById(R.id.work)).getChildAt(0);
                                    ImageView webcam_pic = (ImageView) v2.findViewById(R.id.webcam_picture_in_single_view);
                                    int height=webcam_pic.getLayoutParams().height;
                                    int width=webcam_pic.getLayoutParams().width;
                                    webcam_pic.setImageBitmap(Bitmap.createScaledBitmap(decodedByte, width, height, false)); //TODO
                                }
                            }

                            //((ImageView)findViewById(R.id.Foto)).setImageBitmap(decodedByte);
                            Log.i("websocket", "bitmap set");


                        } catch (Exception e) {
                            int ignore = 0;
                        }
                    } else if (cmd.equals("m2v_login")) {
                        try {
                            int area_id=-1;
                            int client_id=-1;
                            // first check: does this area exist
                            String area_name = object.getString("area");
                            for (int i = 0; i < data.size(); i++) {
                                if(data.get(i).name.equals(area_name)){
                                    area_id=i;
                                    break;
                                }
                            }

                            // if not, generate new area
                            if(area_id==-1){
                                data.append(data.size(), new areas(context, area_name,1));
                                area_id=data.size()-1;
                            }

                            // now check if the client already existed
                            for (int i = 0; i < data.get(area_id).m2mList.size(); i++) {
                                if(data.get(area_id).m2mList.get(i).mid.equals(mid)){
                                    client_id=i;
                                    break;
                                }
                            }

                            // if not, add client to area
                            if(client_id==-1) {
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
                                data.get(area_id).m2mList.add(new m2m_container(mid, state, area_name, detection, new_loc, last_seen, alias));
                            }

                            // and now show it
                            prepare_adapter();

                        } catch (Exception e) {
                            int ignore = 0;
                        }
                    }

                    else if(cmd.equals("state_change")){
                        if(id[0]>-1){
                            try {
                                data.get(id[0]).m2mList.get(id[1]).state = Integer.parseInt(object.getString("state"));
                                mAdapter.setState(id[0],id[1]);
                            } catch(Exception ex){
                                Log.i("Websocket","Exception:"+ex.toString());
                            }
                        }
                    }

                    else if(cmd.equals("m2m_hb")){
                        Log.i("Websocket","Received hb");
                        if(id[0]>-1){
                            try {
                                View v=getView_ifVisible(id[0],id[1],WebcamView);
                                if(v!=null) {
                                    float intermediat = Float.parseFloat(object.getString("ts"));
                                    data.get(id[0]).m2mList.get(id[1]).last_seen = (long) intermediat;
                                    mAdapter.setUpdated(id[0], id[1], (TextView) v.findViewById(R.id.LastUpdated));
                                }
                            } catch(Exception ex){
                                Log.i("Websocket","Exception:"+ex.toString());
                            }
                        }
                    }
                }

            }
        }
    };

    private View getView_ifVisible(int gid, int cid, ExpandableListView WebcamView) {
        // display it or not?
        View x=null;
        View v=null;
        int firstVis = WebcamView.getFirstVisiblePosition();
        int lastVis = WebcamView.getLastVisiblePosition();
        int count = lastVis - firstVis;
        for(int i=0;i<=count;i++) {
            x = WebcamView.getChildAt(i);
            if (x != null) {
                long packedPosition = WebcamView.getExpandableListPosition(i + firstVis);
                int packedPositionType = ExpandableListView.getPackedPositionType(packedPosition);

                if (packedPositionType != ExpandableListView.PACKED_POSITION_TYPE_NULL) {
                    int groupPosition = ExpandableListView.getPackedPositionGroup(packedPosition);
                    if (packedPositionType == ExpandableListView.PACKED_POSITION_TYPE_CHILD) {
                        int childPosition = ExpandableListView.getPackedPositionChild(packedPosition);
                        if(groupPosition==gid && childPosition==cid) {
                            v=x;
                        }
                    }
                }
            }
        }
        return v;
    }

    private int[] mid2id(String mid) {
        int id[] = {-1,-1};
        for (int i = 0; i < data.size(); i++) {
            for (int j = 0; j < data.get(i).m2mList.size(); j++) {
                if (data.get(i).m2mList.get(j).mid.equals(mid)) {
                    id[0] = i;
                    id[1] = j;
                }
            }
        }
        return id;
    }

    private void prepare_adapter(){
        ExpandableListView liste = (ExpandableListView)findViewById(R.id.listScroller);
        if(liste!=null){
            ListAdapter adapter = new ListAdapter(this,data);
            mAdapter = adapter;
            liste.setAdapter(adapter);
        }
        // present all lists unfolded
        for (int position = 0; position < data.size(); position++) {
            liste.expandGroup(position);
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
