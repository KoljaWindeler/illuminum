import org.apache.cordova.CordovaWebView;
import org.apache.cordova.CallbackContext;
import org.apache.cordova.CordovaPlugin;
import org.apache.cordova.CordovaInterface;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;
import android.provider.Settings;
import android.widget.Toast;

import com.glubsch.MainActivity;

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
        Context context = cordova.getActivity();
        SharedPreferences mSettings = (SharedPreferences) context.getSharedPreferences(MainActivity.PREFS_NAME, context.MODE_MULTI_PROCESS);


        if(action.equals("get")) {
            String login = mSettings.getString("LOGIN", "Kolja");
            String pw = mSettings.getString("PW", "hui");
            String quality = "0";
            if(login.equals("") || pw.equals("")) quality="-1";
            parameter.put("q", quality);
            parameter.put("l", login);
            parameter.put("p", pw);
            // callback.success(parameter);
            PluginResult result = new PluginResult(PluginResult.Status.OK, parameter);
            result.setKeepCallback(true);
            callbackContext.sendPluginResult(result);
        } else if (action.equals("set")){
            if(!args.getString(0).equals("") && !args.getString(1).equals("")) {
                SharedPreferences.Editor editor = mSettings.edit();
                editor.putString("LOGIN", args.getString(0));
                editor.putString("PW", args.getString(1));
                editor.commit();
            }
        }
        return true;
    };


}

