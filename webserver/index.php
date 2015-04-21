<?php
///////////////// server status ///////////////////////////
$body='<h1 id="l10n_title">Python WebSocket-Server<br>Status: ';
unset($output);
exec('ps -ax|grep "python3" | grep "main.py"| grep -v "grep"',$output,$return_var);
if(!empty($output[0])){	// python serer is running add everything
	$body.='<font color="green">online</font>';

	$body.='</h1>';
	// add ws display stuff
	$extra_header='<script type="text/javascript">
		var con = null;
		function start() {
		        con = new WebSocket(\'ws://192.168.1.80:9876/\');
			con.onopen = function(){
				login("kolja","huhu");
			};
			// reacting on incoming messages
		        con.onmessage = function(msg) {
                		console.log("Message");
				msg_dec=JSON.parse(msg.data);
				console.log(msg_dec);

				if(msg_dec["cmd"]=="m2v_login"){
					if(document.getElementById("clients")!=undefined){
						var node=document.createElement("P");
						node.appendChild(document.createTextNode("client:"+msg_dec["m2m_client"]));

						var sub_node=document.createElement("P");
						sub_node.setAttribute("id",msg_dec["m2m_client"]+"_hb");

						node.appendChild(sub_node);
						document.getElementById("clients").appendChild(node);
						console.log("hb feld in client angebaut");
					}
				}

				if(msg_dec["cmd"]=="hb"){
					if(document.getElementById(msg_dec["client_id"]+"_hb")!=undefined){
						document.getElementById(msg_dec["client_id"]+"_hb").innerHTML=msg_dec["ts"];
						console.log("hb ts updated");
					}
				}


				if(msg_dec["app"]=="web_cam"){
					if(msg_dec["cmd"]=="pic_ready"){
						if(document.getElementById("webcam_pic")!=undefined){
							document.getElementById("webcam_pic").innerHTML=\'<img src="webcam/dump.jpg">\';
						}
					} else if(msg_dec["cmd"]=="offline" || msg_dec["cmd"]=="online") {
						if(document.getElementById("webcam_status")!=undefined){
							if(msg_dec["cmd"]=="offline"){
								document.getElementById("webcam_status").innerHTML=\'Status: <font color="red">offline</font><br> <a class="button" id="webcam_start" onclick="send(\\\'web_cam\\\',\\\'start\\\')">Start</a><a class="button" id="webcam_oneshot" onclick="send(\\\'web_cam\\\',\\\'single\\\')">Single Shot</a>\';
							} else if(msg_dec["cmd"]=="online"){
								document.getElementById("webcam_status").innerHTML=\'Status: <font color="green">online</font> <div id="webcam_detection_status"></div><a class="button" id="webcam_start" onclick="send(\\\'web_cam\\\',\\\'detection_start\\\')">On</a><a class="button" id="webcam_start" onclick="send(\\\'web_cam\\\',\\\'detection_pause\\\')">Off</a>\';
								document.getElementById("webcam_pic").innerHTML=\'\';
							}
						}
					} else if(msg_dec["cmd"]=="detection_activ" || msg_dec["cmd"]=="detection_inactiv"){
						console.log("detection bla");
						if(document.getElementById("webcam_detection_status")!=undefined){
							console.log("element found");
							document.getElementById("webcam_detection_status").innerHTML=msg_dec["cmd"];
						}
					}
				} else if(msg_dec["app"]=="ws"){
					if(msg_dec["cmd"]=="update_time"){
						if(document.getElementById("track")!=undefined){
							document.getElementById("track").innerHTML = msg_dec["data"];
						}
					}
				}
			}

	        }
		function login(user,pw) {
			console.log("send login");
			if(con == null){
				return;
			}
			var cmd_data = { "cmd":"login", "login":user, "pw":pw};
			console.log(JSON.stringify(cmd_data));
			con.send(JSON.stringify(cmd_data));
		}

		function send(app,cmd) {
			console.log("send");
			console.log("app:"+app);
			console.log("cmd:"+cmd);
			if(con == null) {
				return;
			}
	
			var cmd_data = { "cmd":cmd, "app":app};
			console.log(JSON.stringify(cmd_data));
			con.send(JSON.stringify(cmd_data));
		}
		</script>';
	$body.='<br>';
	
	// add webcam stuff
	//$body.='<h1 id="l10n_title">WebCam-Server';
	//$body.='<div id="webcam_status">Status: -</div>';
	//$body.='<dir id="webcam_pic"></div>';
	//$body.='</h1>';
	$body.='<h1 id="l10n_title">Clients</h1>';
	$body.='<div id="clients"></div>';

	// add reboot button
	$body.='<h1 id="l10n_title">Controll</h1>';
	$body.='<a class="button" id="webcam_start" onclick="login(\'kolja\',\'huhu\')">Login</a>';
	
} else { //python server is not running just add start button
	$body.='<font color="red">offline</font> &nbsp; ';
	$body.='<a class="button" href="http://'.$_SERVER[HTTP_HOST].$_SERVER[REQUEST_URI].'?start_python">Start server</a>';
}

///////////////// server status ///////////////////////////

///////////////// header ///////////////////////////
$header='<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en"><head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta http-equiv="x-dns-prefetch-control" content="off">
        <meta name="robots" content="noindex">
        <link rel="stylesheet" href="status_blue.css" type="text/css" media="screen" charset="utf-8">
        <title></title>
	'.$extra_header.'
    </head>
    <body onload="start()">
        <table height="100%" width="100%">
            <tbody><tr>
                <td align="center" valign="middle">';
$footer='</td></tr></tbody></table></body></html>';
///////////////// header ///////////////////////////
echo $header;
echo $body;
echo $footer;
?>

