var exec = require('cordova/exec');
function GetLogin() { console.log("GetLogin.js: is created");	}
	GetLogin.prototype.showToast = 
		function(aString){ 
			console.log("GetLogin.js: showToast"); 
			exec(
				function(result){ /*alert("OK" + reply);*/ 	}, 
				function(result){ /*alert("Error" + reply);*/ 	},
				"GetLogin",
				aString,
				[]
			);
} 
var GetLogin = new GetLogin(); 
module.exports = GetLogin;
