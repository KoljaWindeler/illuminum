cordova.define('cordova/plugin_list', function(require, exports, module) {
module.exports = [
    {
        "file": "plugins/cordova-plugin-whitelist/whitelist.js",
        "id": "cordova-plugin-whitelist.whitelist",
        "runs": true
    },
    {
        "file": "plugins/com.glubsch.get_login_plugin/www/GetLogin.js",
        "id": "com.glubsch.get_login_plugin.GetLoginPlugin",
        "clobbers": [
            "GetLogin"
        ]
    }
];
module.exports.metadata = 
// TOP OF METADATA
{
    "cordova-plugin-whitelist": "1.0.0",
    "com.glubsch.get_login_plugin": "0.2.12"
}
// BOTTOM OF METADATA
});