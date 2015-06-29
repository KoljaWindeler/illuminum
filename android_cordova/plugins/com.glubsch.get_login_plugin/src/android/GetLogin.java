import org.apache.cordova.CordovaWebView;
import org.apache.cordova.CallbackContext;
import org.apache.cordova.CordovaPlugin;
import org.apache.cordova.CordovaInterface;
import android.util.Log;
import android.provider.Settings;
import android.widget.Toast;
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
        Log.v(TAG,"CoolPlugin received:"+ action);
        cordova.getActivity().runOnUiThread(new Runnable() {
            public void run() {
                Toast toast = Toast.makeText(cordova.getActivity().getApplicationContext(), action, duration);
                toast.show();
            }
        });
        return true;
    }
}

