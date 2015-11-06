cordova.define(
	"com.glubsch.get_login_plugin.GetLoginPlugin", 
	function(require, exports, module) { 
		var exec = require('cordova/exec');
		function GetLogin() { 
			console.log("CoolPlugin.js: is created");
		}
		GetLogin.prototype.showToast = function(aString){ 
			console.log("CoolPlugin.js: showToast"); 
			exec(
				function(result){ /*alert("OK" + reply);*/ }, 
				function(result){ /*alert("Error" + reply);*/ },
				"GetLogin",
				aString,
				[]
			);
		} 

		var GetLogin = new GetLogin(); 
		module.exports = GetLogin;
	}
);
