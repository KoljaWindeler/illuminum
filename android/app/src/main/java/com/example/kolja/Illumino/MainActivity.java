package com.example.kolja.Illumino;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.app.Activity;
import android.util.Log;
import android.content.Context;
import android.view.View;
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

import java.util.Vector;

import android.widget.ListView;



public class MainActivity extends Activity implements android.view.View.OnClickListener {
    public static final String PREFS_NAME = "IlluminoSettings";
    Vector<ListContainer> res_data = new Vector<ListContainer>();
    SharedPreferences settings;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Intent intent = new Intent(this, bg_service.class);
        startService(intent);

        settings = getSharedPreferences(PREFS_NAME, 0);
        String login =settings.getString("LOGIN","Kolja");
        ((Button)findViewById(R.id.save_id)).setOnClickListener(this);
        ((EditText)findViewById(R.id.id)).setText(login);


    }

    @Override
    public void onClick(View arg0) {
        Intent intent;
        switch (arg0.getId()) {
            case R.id.save_id:
                String login=((EditText)findViewById(R.id.id)).getText().toString();
                SharedPreferences.Editor editor = settings.edit();
                editor.putString("LOGIN", login);
                editor.commit();
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
                if(bundle.containsKey(s_ws.JSON)) {
                    String data = bundle.getString(s_ws.JSON);
                    String cmd;
                    //int resultCode = bundle.getInt(DownloadService.RESULT);
                    TextView textView = (TextView) findViewById(R.id.log);
                    //textView.setText(textView.getText() + "\n" + data);

                    try {
                        String log = bundle.getString(bg_service.LOG);
                        if (log.equals("log")) {
                            textView.setText(String.valueOf(bundle.getFloat(s_ws.JSON)) + "\n" + textView.getText());
                        }
                    } catch (Exception e) {
                        int ignore = 1;
                    }

                    JSONObject object = new JSONObject();

                    try {
                        object = new JSONObject(data);
                        cmd = object.getString("cmd");
                    } catch (Exception e) {
                        cmd = "";
                    }

                    if (cmd.equals("rf")) {
                        try {
                            Long tsLong = System.currentTimeMillis();


                            String encodedImage = object.getString("img");
                            Log.i("websocket", "got str from obj");
                            byte[] decodedString = Base64.decode(encodedImage, Base64.NO_OPTIONS);
                            Log.i("websocket", "decoded");
                            Bitmap decodedByte = BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length);
                            Log.i("websocket", "loaded bitmap");

                            int id = -1;
                            for (int i = 0; i < res_data.size(); i++) {
                                if (res_data.elementAt(i).name.equals(object.getString("mid"))) {
                                    id = i;
                                }
                            }
                            if (id > -1) {
                                ListView WebcamView = (ListView) findViewById(R.id.listScroller);
                                View v = WebcamView.getChildAt(id);
                                ((ImageView) v.findViewById(R.id.webcam)).setImageBitmap(decodedByte);
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
                            String mid = object.getString("mid");
                            String area = object.getString("s_area");
                            int state = object.getInt("state");
                            String account = object.getString("account");

                            prepare_adapter(mid);

                            // quick and dirty: add us to the list of webcams as soon as they sign up:
//                        JSONObject object_send = new JSONObject();
//                        object_send.put("cmd", "set_interval");
//                        object_send.put("mid", mid);
//                        object_send.put("interval", 1);
//
//                        Intent send_intent = new Intent(bg_service.SENDER);
//                        send_intent.putExtra(bg_service.JSON, object_send.toString());
//                        sendBroadcast(send_intent);

                        } catch (Exception e) {
                            int ignore = 0;
                        }
                    }
                }

            }
        }
    };

    private void prepare_adapter(String mid){
        ListView liste = (ListView)findViewById(R.id.listScroller);
        if(liste!=null){
            res_data.add(new ListContainer(mid,0,true,0));

            // darstellen
            ListContainer temp_array[]= new ListContainer[res_data.size()];
            for(int i=0; i<res_data.size();i++){
                temp_array[i]=res_data.elementAt(i);
                temp_array[i].name=res_data.elementAt(i).name;
            }

            ListAdapter adapter = new ListAdapter(this,R.layout.listentry,temp_array);
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
