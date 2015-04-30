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
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.net.URI;
import java.net.URISyntaxException;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;


public class MainActivity extends ActionBarActivity {
    private WebSocketClient mWebSocketClient;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        connectWebSocket();
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
                        TextView textView = (TextView)findViewById(R.id.messages);
                        textView.setText(textView.getText() + "\n" + message);
						
			JSONObject object = new JSONObject();
			object.fromString(message);
			try {
				cmd=object.getString("cmd");
			} catch (e) {
				cmd=""
			}
			
			if(cmd=="rf"){					
				try {
					String encodedImage=object.getString("data");
					Log.i("websocket","got str from obj");
					byte[] decodedString = Base64.decode(encodedImage, Base64.URL_SAFE);
					Log.i("websocket","decoded");
					Bitmap decodedByte = BitmapFactory.decodeByteArray(decodedString, 0, decodedString.length);
					Log.i("websocket","loaded bitmap");
					(Image)findViewById(R.id.img).setImageBitmap(decodedByte);
					Log.i("websocket","bitmap set");
				}	catch (e) {
					int ignore=0;
				}
			}
			
			else if(cmd=="m2v_login"){
				try {
					// add an object that will hold the ID "mid", "area","state","account"
					String mid=object.getString("mid");
					String area=object.getString("area");
					int state=object.getString("state");
					String account=object.getString("account");
					
					// quick and dirty: add us to the list of webcams as soon as they sign up:
					JSONObject object_send = new JSONObject();
					object_send.put("cmd", "set_interval");
					object_send.put("mid", mid);
					object_send.put("interval", "3");
					mWebSocketClient.send(object_send.toString());
				}	catch (e) {
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
