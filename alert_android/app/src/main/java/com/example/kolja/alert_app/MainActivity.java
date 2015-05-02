package com.example.kolja.alert_app;

import android.os.Bundle;
import android.support.v7.app.ActionBarActivity;
import android.view.Menu;
import android.view.MenuItem;
import android.app.Activity;
import android.app.Fragment;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;
import android.media.Image;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.view.View.OnClickListener;
import org.java_websocket.util.Base64;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.net.URI;
import java.net.URISyntaxException;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.Vector;
import android.app.ActionBar;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.ActionBar.Tab;
import android.app.ActionBar.TabListener;
import android.app.FragmentTransaction;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.Window;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;


public class MainActivity extends Activity implements android.view.View.OnClickListener {
    private WebSocketClient mWebSocketClient;
    Vector<ListContainer> res_data = new Vector<ListContainer>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        connectWebSocket();
    }

    @Override
    public void onClick(View arg0) {
        Intent intent;
        //switch (arg0.getId()) {
        //    case R.id.scenario_create:
        //        break;
        //};
    };

    private void prepare_adapter(String mid){
        ListView lichter_listView = (ListView)findViewById(R.id.listScroller);
        if(lichter_listView!=null){
            res_data.add(new ListContainer(mid,0,true,0));

            // darstellen
            ListContainer temp_array[]= new ListContainer[res_data.size()];
            for(int i=0; i<res_data.size();i++){
                temp_array[i]=res_data.elementAt(i);
                temp_array[i].name=res_data.elementAt(i).name;
            }

            ListAdapter adapter = new ListAdapter(this,R.layout.listentry,temp_array);
            lichter_listView.setAdapter(adapter);
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
            public void onMessage(String s) {
                final String message = s;
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        //TextView textView = (TextView)findViewById(R.id.log);
                        //textView.setText(textView.getText() + "\n" + message);
                        String cmd;
                        JSONObject object = new JSONObject();

                        try {
                            object = new JSONObject(message);
                            cmd=object.getString("cmd");
                        } catch (Exception e) {
                            cmd="";
                        }

                        if(cmd.equals("rf")){
                            try {
                                Long tsLong = System.currentTimeMillis();


                                String encodedImage=object.getString("img");
                                Log.i("websocket","got str from obj");
                                byte[] decodedString = Base64.decode(encodedImage, Base64.NO_OPTIONS);
                                Log.i("websocket","decoded");
                                Bitmap decodedByte = BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length);
                                Log.i("websocket","loaded bitmap");

                                int id=-1;
                                for(int i=0;i<res_data.size();i++){
                                    if(res_data.elementAt(i).name.equals(object.getString("mid"))){
                                        id=i;
                                    }
                                }
                                if(id>-1) {
                                    ListView WebcamView = (ListView) findViewById(R.id.listScroller);
                                    View v = WebcamView.getChildAt(id);
                                    ((ImageView) v.findViewById(R.id.webcam)).setImageBitmap(decodedByte);
                                }

                                //((ImageView)findViewById(R.id.Foto)).setImageBitmap(decodedByte);
                                Log.i("websocket","bitmap set");

                                Long tsLong2 = System.currentTimeMillis()-tsLong;
                                String ts = tsLong2.toString();
                                //textView.setText(textView.getText() + "\n" + ts);

                            }	catch (Exception e) {
                                int ignore=0;
                            }
                        }

                        else if(cmd.equals("m2v_login")){
                            try {
                                // add an object that will hold the ID "mid", "area","state","account"
                                String mid=object.getString("mid");
                                String area=object.getString("area");
                                int state=object.getInt("state");
                                String account=object.getString("account");

                                prepare_adapter(mid);

                                // quick and dirty: add us to the list of webcams as soon as they sign up:
                                JSONObject object_send = new JSONObject();
                                object_send.put("cmd", "set_interval");
                                object_send.put("mid", mid);
                                object_send.put("interval", 1);
                                mWebSocketClient.send(object_send.toString());
                            }	catch (Exception e) {
                                int ignore=0;
                            }
                        }

                    }
                });
            }

            @Override
            public void onClose(int i, String s, boolean b) {
                Log.i("Websocket", "Closed " + s);
            }

            @Override
            public void onError(Exception e) {
                Log.i("Websocket", "Error " + e.getMessage());
            }
        };
        mWebSocketClient.connect();
    }
}
