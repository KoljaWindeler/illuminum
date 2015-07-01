import org.apache.cordova.CordovaWebView;
import org.apache.cordova.CallbackContext;
import org.apache.cordova.CordovaPlugin;
import org.apache.cordova.CordovaInterface;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.util.Log;
import android.provider.Settings;
import android.widget.Toast;

import com.glubsch.MainActivity;
import com.glubsch.bg_service;

import org.apache.cordova.PluginResult;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
public class GetLogin extends CordovaPlugin {
    public static final String TAG = "GetLogin";
    /**
     * Constructor.
     */
    public GetLogin() {}
    /**
     * Sets the context of the Command. This can then be used to do things like
     * get file paths associated with the Activity.
     *
     * @param cordova The context of the main Activity.
     * @param webView The CordovaWebView Cordova is running in.
     */
    public void initialize(CordovaInterface cordova, CordovaWebView webView) {
        super.initialize(cordova, webView);
        Log.v(TAG,"Init GetLogin");
    }
    public boolean execute(final String action, JSONArray args, CallbackContext callbackContext) throws JSONException {
        final int duration = Toast.LENGTH_SHORT;
        // Shows a toast
        /*Log.v(TAG,"CoolPlugin received:"+ action);
        cordova.getActivity().runOnUiThread(new Runnable() {
            public void run() {
                Toast toast = Toast.makeText(cordova.getActivity().getApplicationContext(), action, duration);
                toast.show();
            }
        });*/
        JSONObject parameter = new JSONObject();
        PluginResult result = null;
        Context context = cordova.getActivity();
        SharedPreferences mSettings = (SharedPreferences) context.getSharedPreferences(MainActivity.PREFS_NAME, context.MODE_MULTI_PROCESS);
        Log.v("glubsch I/chromium","->execute plugin, action:"+action);

        if(action.equals("get")) {
            String login = mSettings.getString("LOGIN", "Kolja");
            String pw = mSettings.getString("PW", "hui");
            //login="kolja";
            //pw="hui";
            String quality = "0";
            if(login.equals("") || pw.equals("")) quality="-1";
            if(login.equals("-1") || pw.equals("-1")) quality="-1";
            parameter.put("q", quality);
            parameter.put("l", login);
            parameter.put("p", pw);
            Log.v("glubsch I/chromium","sending login data, user:"+login+" and pw:"+pw);
            result = new PluginResult(PluginResult.Status.OK, parameter);
            // callback.success(parameter);
        } else if (action.equals("set")){
            Log.v("glubsch I/chromium","saving login data, user:"+args.getString(0)+" and pw:"+args.getString(1));
            String login = mSettings.getString("LOGIN", "Kolja");
            String pw = mSettings.getString("PW", "hui");
            if(!args.getString(0).equals(login) || !args.getString(1).equals(pw)) {
                SharedPreferences.Editor editor = mSettings.edit();

                login=args.getString(0);
                pw=args.getString(1);
                if(login.equals("") || pw.equals("")){
                    login="-1";
                    pw="-1";
                }

                editor.putString("LOGIN", login);
                editor.putString("PW", pw);
                editor.commit();

                //Intent intent = new Intent(context, bg_service.class);
                //context.stopService(intent);
                Log.v("glubsch I/chromium","SAFED");
            }
            result = new PluginResult(PluginResult.Status.OK, 0);
        }
        callbackContext.sendPluginResult(result);

        return true;
    };


}

