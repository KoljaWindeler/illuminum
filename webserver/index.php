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
                		// console.log("Message");
				msg_dec=JSON.parse(msg.data);
				// console.log(msg_dec);

				if(msg_dec["cmd"]=="m2v_login"){
					if(document.getElementById("clients")!=undefined){
					    console.log("suche nach gruppe "+msg_dec["account"]+"_"+msg_dec["area"]);
						var area=document.getElementById(msg_dec["account"]+"_"+msg_dec["area"]);
						if(area==undefined){
						    console.log("nicht gefunden, lege sie an");
							var node=document.createElement("P");
							node.appendChild(document.createTextNode("Area:"+msg_dec["account"]+"_"+msg_dec["area"]+""));
							node.setAttribute("id",msg_dec["account"]+"_"+msg_dec["area"]);

							var button=document.createElement("A");
							button.setAttribute("id",+msg_dec["account"]+"_"+msg_dec["area"]+"_on");
							button.onclick=function(){
								var msg_int=msg_dec;
								return function(){
									set_detection(msg_int["account"],msg_int["area"],2);
								}
							   }();
							button.className="button";
							button.text="Detection on";
							node.appendChild(button);

							button=document.createElement("A");
							button.setAttribute("id",+msg_dec["account"]+"_"+msg_dec["area"]+"_off");
							button.onclick=function(){
								var msg_int=msg_dec;
								return function(){
									set_detection(msg_int["account"],msg_int["area"],0);
								}
							   }();
							button.className="button";
							button.text="Detection off";
							node.appendChild(button);

							document.getElementById("clients").appendChild(node);
							area=node;
						}

						var node=document.getElementById(msg_dec["mid"]);
						if(node==undefined){
						    console.log("knoten! nicht gefunden, lege ihn an");
							node=document.createElement("P");
							node.appendChild(document.createTextNode("client:"+msg_dec["alias"]+" / "+msg_dec["mid"]));
							node.setAttribute("id",msg_dec["mid"]);
							

							var button=document.createElement("A");
							button.setAttribute("id",+msg_dec["mid"]+"_set_interval_2");
							button.onclick=function(){
								var msg_int=msg_dec;
								return function(){
									set_interval(msg_int["mid"],0.01);
								}
							   }();
							button.className="button";
							button.text="Webcam 0.1s";
							node.appendChild(button);

							var button=document.createElement("A");
							button.setAttribute("id",+msg_dec["mid"]+"_set_interval_2");
							button.onclick=function(){
								var msg_int=msg_dec;
								return function(){
									set_interval(msg_int["mid"],1);
								}
							   }();
							button.className="button";
							button.text="Webcam 1s";
							node.appendChild(button);

							var button=document.createElement("A");
							button.setAttribute("id",+msg_dec["mid"]+"_set_interval_2");
							button.onclick=function(){
								var msg_int=msg_dec;
								return function(){
									set_interval(msg_int["mid"],5);
								}
							   }();
							button.className="button";
							button.text="Webcam 5s";
							node.appendChild(button);


							button=document.createElement("A");
							button.setAttribute("id",+msg_dec["mid"]+"_set_interval_0");
							button.onclick=function(){
								var msg_int=msg_dec;
								return function(){
									set_interval(msg_int["mid"],0);
								}
							   }();
							button.className="button";
							button.text="Webcam off";
							node.appendChild(button);

							var sub_node=document.createElement("P");
							sub_node.setAttribute("id",msg_dec["mid"]+"_hb");
							node.appendChild(sub_node);

							sub_node=document.createElement("P");
							sub_node.setAttribute("id",msg_dec["mid"]+"_state");
							node.appendChild(sub_node);

							area.appendChild(node);
							console.log("hb feld in client angebaut");
						}

						document.getElementById(msg_dec["mid"]+"_state").innerHTML=state2str((msg_dec["state"]))+", "+det2str(msg_dec["detection"]);
					}
				}

				else if(msg_dec["cmd"]=="hb"){
					if(document.getElementById(msg_dec["mid"]+"_hb")!=undefined){
						document.getElementById(msg_dec["mid"]+"_hb").innerHTML=msg_dec["ts"];
						console.log("hb ts updated");
					}
				}

				else if(msg_dec["cmd"]=="state_change"){
					e=document.getElementById(msg_dec["mid"]+"_state");
					state=msg_dec["state"];
					detection=msg_dec["detection"];
					if(e!=undefined){
						e.innerHTML=state2str(state)+" "+det2str(detection);
					}
				}

				else if(msg_dec["cmd"]=="rf"){
					var client=document.getElementById(msg_dec["mid"]);
					if(client!=undefined){
						if(document.getElementById(msg_dec["mid"]+"_img")==undefined){
							var sub_node=document.createElement("img");
							sub_node.setAttribute("id",msg_dec["mid"]+"_img");
							client.appendChild(sub_node);
						}
					}

					img=document.getElementById(msg_dec["mid"]+"_img");
					if(img!=undefined){
						if(msg_dec["img"]!=""){
							img.src="data:image/png;base64,"+msg_dec["img"];
						} else if(msg_dec["path"]!=""){
							img.src="http://192.168.1.80/"+msg_dec["path"];
						};

					} else {
						alert("konnte mid_img nicht finden!!");
					};
				}

				else if(msg_dec["cmd"]=="disconnect"){
					var area=document.getElementById(msg_dec["account"]+"_"+msg_dec["area"]);
					var client=document.getElementById(msg_dec["mid"]);
                                        if(area!=undefined){
						console.log("area gefunden");
						if(client!=undefined){
							console.log("client gefunden");
							document.getElementById(msg_dec["mid"]+"_state").innerHTML="disconnected"
							//area.removeChild(client);
							console.log("entfernt");
						}
					}
				}

			}

	        }

		function state2str(state){
			if(state==0){
				return "idle";
			} else if(state==1){
				return "movement!";
			} else if(state==-1){
				return "disconnected";
			} else {
				return state.toString();
			};
		};

		function det2str(det){
		    if(det==0){
		        return "detection off";
		    } else if(det==1){
		        return "detection on";
		    } else if(det==2){
		        return "detection very on";
		    } else {
		        return det.toString();
		    }
		}

		function set_interval(mid,interval){
			if(con == null){
				return;
			}
			var cmd_data = { "cmd":"set_interval", "mid":mid, "interval":interval};
			console.log(JSON.stringify(cmd_data));
			con.send(JSON.stringify(cmd_data));

			var client=document.getElementById(mid);
			if(interval==0){
				var img=document.getElementById(mid+"_img");
				if(client!=undefined){
					if(img!=undefined){
						setTimeout(function(){
							//do what you need here
							client.removeChild(img);
						}, 1000)
					}
				}
			} else {
				if(document.getElementById(mid+"_img")==undefined){
					var sub_node=document.createElement("img");
					sub_node.setAttribute("id",mid+"_img");
					client.appendChild(sub_node);
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

		function set_detection(user,area,on_off){
			if(con == null) {
				return;
			}
			var cmd_data = { "cmd":"detection", "state":on_off, "area":area, "user":user};
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
	//$body.='<h1 id="l10n_title">Controll</h1>';
	//$body.='<a class="button" id="detection_start" onclick="send(\'detection\',\'on\')">Detection on</a>';
	//$body.='<a class="button" id="detection_stop" onclick="send(\'detection\',\'off\')">Detection off</a>';
	
} else { //python server is not running just add start button
	$body.='<font color="red">offline</font> &nbsp; ';
	#$body.='<a class="button" href="http://'.$_SERVER[HTTP_HOST].$_SERVER[REQUEST_URI].'?start_python">Start server</a>';
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

