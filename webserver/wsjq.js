var con = null;
var f_t= 0;
var c_t=0;


$(function(){
	open_ws();
});


function open_ws() {
	con = new WebSocket('ws://192.168.1.80:9876/');
	con.onopen = function(){
		login("browser","hui");
	};

	// reacting on incoming messages
	con.onmessage = function(msg) {
		// console.log("Message");
		msg_dec=JSON.parse(msg.data);
		parse_msg(msg_dec);
	};
};


	
function parse_msg(msg_dec){
	// console.log(msg_dec);
	if(msg_dec["cmd"]=="m2v_login"){
		check_append_m2m(msg_dec);
	}

	else if(msg_dec["cmd"]=="hb"){
		if($("#"+msg_dec["mid"]+"_hb")!=undefined){
			var delay=Date.now()-(1000*parseFloat(msg_dec["ts"]));
			$("#"+msg_dec["mid"]+"_hb").innerHTML=msg_dec["ts"]+" delay "+delay+" ms";
			console.log("hb ts updated");
		}
	}

	else if(msg_dec["cmd"]=="state_change"){
		e=$("#"+msg_dec["mid"]+"_state");
		state=msg_dec["state"];
		detection=msg_dec["detection"];
		if(e!=undefined){
			e.innerHTML=state2str(state)+" || "+det2str(detection);
		}
	}

	else if(msg_dec["cmd"]=="rf"){
		console.log("rf message received");
		var delay=parseInt(Date.now()-(1000*parseFloat(msg_dec["ts"])));
		c_t=c_t+1;
		if(f_t==0){
			f_t=Date.now();
		}
		var fps=Math.floor((c_t/((Date.now()-f_t)/1000)*100))/100;
		$("#"+msg_dec["mid"]+"_hb").innerHTML="Foto age "+delay+" ms, fps: "+fps;


		var client=$("#"+msg_dec["mid"]);
		if(client.length){
			show_liveview(msg_dec["mid"]);
		}
		console.log("searching image");
		img=$("#"+msg_dec["mid"]+"_liveview_pic");
		if(img.length){
			console.log("image found");
			console.log(msg_dec);
			if(msg_dec["img"]!=""){
				console.log("content found");
				img.attr("src","data:image/jpeg;base64,"+msg_dec["img"]);
			} else if(msg_dec["path"]!=""){
				img.src="http://192.168.1.80/"+msg_dec["path"];
			};

		} else {
			alert("konnte mid_img nicht finden!!");
		};
	}

	else if(msg_dec["cmd"]=="disconnect"){
		var area=$("#"+msg_dec["account"]+"_"+msg_dec["area"]);
		var client=$("#"+msg_dec["mid"]);
							if(area!=undefined){
			console.log("area gefunden");
			if(client!=undefined){
				console.log("client gefunden");
				$("#"+msg_dec["mid"]+"_state").innerHTML="disconnected"
				//area.removeChild(client);
				console.log("entfernt");
			}
		}
	}
}


function check_append_m2m(msg_dec){
	console.log(msg_dec);
	// get root clients node
	if($("#clients").length){
		console.log("suche nach gruppe "+msg_dec["account"]+"_"+msg_dec["area"]);
		var area=$("#"+msg_dec["account"]+"_"+msg_dec["area"]);
		// check if area is already existing
		if(area.length==0){
			
			
			/////////////////// CREATE AREA ////////////////////////////(
			var node=$("<p></p>");
			node.attr({
				"id" : msg_dec["account"]+"_"+msg_dec["area"],
				"class": "area_header"
			});
			
			var text=$("<p></p>").text(msg_dec["area"]);
			text.attr({
				"id" : msg_dec["account"]+"_"+msg_dec["area"]+"_title",
				"class": "area_title"
			});
			node.append(text);
			
			text=$("<p></p>").text(det2str(msg_dec["detection"]));
			text.attr({
				"id" : msg_dec["account"]+"_"+msg_dec["area"]+"_status",
				"class": "area_status"
			});
			node.append(text);
			
			var button=document.createElement("A");
			button.setAttribute("id",+msg_dec["account"]+"_"+msg_dec["area"]+"_on");
			button.className="button";
			button.text="Detection on";
			button.onclick=function(){
				var msg_int=msg_dec;
				return function(){
					set_detection(msg_int["account"],msg_int["area"],"*");
				}
			   }();

			node.append(button);

			button=document.createElement("A");
			button.setAttribute("id",+msg_dec["account"]+"_"+msg_dec["area"]+"_off");
			button.onclick=function(){
				var msg_int=msg_dec;
				return function(){
					set_detection(msg_int["account"],msg_int["area"],"/");
				}
			   }();
			button.className="button";
			button.text="Detection off";
			node.append(button);

			$("#clients").append(node);
			area=node;
			/////////////////// CREATE AREA ////////////////////////////(
		}
	}

	var node=$("#"+msg_dec["mid"]);
	// check if this m2m already exists
	if(!node.length){
		/////////////////// CREATE M2M ////////////////////////////(
		console.log("knoten! nicht gefunden, lege ihn an");
		node=$("<p></p>").text(msg_dec["alias"]);
		node.attr({
			"id":msg_dec["mid"],
			"class":"area_m2m"
		});
		
		var text=$("<div></div>").text(state2str(msg_dec["state"]));
		text.attr({
			"id" : msg_dec["mid"]+"_state",
			"class": "m2m_text"
		});
		node.append(text);
			
		text=$("<div></div>").text("Last ping:"+msg_dec["last_seen"]);
		text.attr({
			"id" : msg_dec["mid"]+"_lastseen",
			"class": "m2m_text"
		});
		node.append(text);

		var button=document.createElement("A");
		button.setAttribute("id",+msg_dec["mid"]+"_toggle_liveview");
		button.onclick=function(){
			var msg_int=msg_dec;
			return function(){
				toggle_liveview(msg_int["mid"]);
			}
		}();
		button.className="button";
		button.text="Livestream";
		node.append(button);
		
		button=document.createElement("A");
		button.setAttribute("id",+msg_dec["mid"]+"_toggle_lightcontrol");
		button.onclick=function(){
			var msg_int=msg_dec;
			return function(){
				toggle_lightcontrol(msg_int["mid"]);
			}
		}();
		button.className="button";
		button.text="lightcontrol";
		node.append(button);
		
		button=document.createElement("A");
		button.setAttribute("id",+msg_dec["mid"]+"_toggle_alarms");
		button.onclick=function(){
			var msg_int=msg_dec;
			return function(){
				toggle_alarms(msg_int["mid"]);
			}
		}();
		button.className="button";
		button.text="alarms";
		node.append(button);
		
		//var cs=document.createElement("input");
		//cs.setAttribute("id",+msg_dec["mid"]+"_img");
		//cs.className="color";
		//cs.value="66ff00";
		//node.append(cs);

		/*button=document.createElement("A");
		button.setAttribute("id",+msg_dec["mid"]+"_set_interval_2");
		button.onclick=function(){
			var msg_int=msg_dec;
			return function(){
				set_interval(msg_int["mid"],0.01);
			}
		}();
		button.className="button";
		button.text="Webcam 0.1s";
		node.append(button);

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
		node.append(button);

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
		node.append(button);


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
		node.append(button);*/

		////////////////// LIVE VIEW ////////////////////////////
		liveview=$("<div></div>").text("this is the liveview");
		liveview.attr({
			"id" : msg_dec["mid"]+"_liveview",
		});
		liveview.hide();
		node.append(liveview);
		
		var img=$("<img></img>");
		img.attr({
			"src" : "https://www.google.de/images/srpr/logo11w.png",
			"id" : msg_dec["mid"]+"_liveview_pic",
		});
		liveview.append(img);
		////////////////// LIVE VIEW ////////////////////////////
		
		////////////////// COLOR SLIDER ////////////////////////////
		lightcontrol=$("<div></div>").text("this is the lightcontrol");
		lightcontrol.attr({
			"id" : msg_dec["mid"]+"_lightcontrol",
		});
		lightcontrol.hide();
		node.append(lightcontrol);
		
		var img=$("<img></img>");
		img.attr({
			"src" : "https://www.google.de/images/srpr/logo11w.png",
		});
		lightcontrol.append(img);
		
		var slider=$("<div></div>");
		slider.attr({
			"style" : "width: 300px",
			"id": "slider1"
		});
		lightcontrol.append(slider);
		
		$('#slider1').slider({min:10, max:100, value:20});
		////////////////// COLOR SLIDER ////////////////////////////
		
		////////////////// ALARM MANAGER ////////////////////////////
		alarms=$("<div></div>").text("this is the alarms");
		alarms.attr({
			"id" : msg_dec["mid"]+"_alarms",
		});
		alarms.hide();
		node.append(alarms);
		
		var img=$("<img></img>");
		img.attr({
			"src" : "https://www.google.de/images/srpr/logo11w.png",
		});
		alarms.append(img);
		////////////////// ALARM MANAGER ////////////////////////////
		//<div style="width: 300px;" id="slider1"></div>
		
		
		area.append(node);
		console.log("hb feld in client angebaut");
		/////////////////// CREATE M2M ////////////////////////////(
	}
	$("#"+msg_dec["mid"]+"_state").innerHTML=state2str((msg_dec["state"]))+" || "+det2str(msg_dec["detection"]);
}

function toggle_liveview(mid){
	var view = $("#"+mid+"_liveview");
	if(view.is(":visible")){
		hide_liveview(mid);
	} else {
		show_liveview(mid)
	};
};

function hide_liveview(mid){
	var view = $("#"+mid+"_liveview");
	if(view.is(":visible")){
		view.fadeOut("fast");
		set_interval(mid,0);
	}
}

function show_liveview(mid){
	hide_lightcontrol(mid);
	hide_alarms(mid);
	var view = $("#"+mid+"_liveview");
	if(!view.is(":visible")){
		view.fadeIn("fast");
		set_interval(mid,1);
	};
}

function toggle_lightcontrol(mid){
	var view = $("#"+mid+"_lightcontrol");
	if(view.is(":visible")){
		hide_lightcontrol(mid);
	} else {
		show_lightcontrol(mid)
	};
};

function hide_lightcontrol(mid){
	var view = $("#"+mid+"_lightcontrol");
	if(view.is(":visible")){
		view.fadeOut("fast");
	}
}

function show_lightcontrol(mid){
	hide_liveview(mid);
	hide_alarms(mid);
	var view = $("#"+mid+"_lightcontrol");
	if(!view.is(":visible")){
		view.fadeIn("fast");
	};
}

function toggle_alarms(mid){
	var view = $("#"+mid+"_alarms");
	if(view.is(":visible")){
		hide_alarms(mid);
	} else {
		show_alarms(mid)
	};
};

function hide_alarms(mid){
	var view = $("#"+mid+"_alarms");
	if(view.is(":visible")){
		view.fadeOut("fast");
	}
}

function show_alarms(mid){
	hide_lightcontrol(mid);
	hide_liveview(mid);
	var view = $("#"+mid+"_alarms");
	if(!view.is(":visible")){
		view.fadeIn("fast");
	};
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
		return "Not protected";
	} else if(det==1){
		return "Protected";
	} else if(det==2){
		return "Very protected";
	} else {
		return det.toString();
	}
}


function updateInfo(color) {
	var cmd_data = { "cmd":"set_color", "r":parseInt(parseFloat(color.rgb[0])*100), "g":parseInt(parseFloat(color.rgb[1])*100), "b":parseInt(parseFloat(color.rgb[2])*100)};
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
}


function set_interval(mid,interval){
	if(con == null){
		return;
	}
	var cmd_data = { "cmd":"set_interval", "mid":mid, "interval":interval};
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));

	var client=$("#"+mid);
	if(interval==0){
		var img=$("#"+mid+"_img");
		if(client!=undefined){
			if(img!=undefined){
				setTimeout(function(){
					//do what you need here
					client.removeChild(img);
				}, 1000)
			}
		}
	} else {
		if($("#"+mid+"_img")==undefined){
			var sub_node=document.createElement("img");
			sub_node.setAttribute("id",mid+"_img");
			client.append(sub_node);
		}
	}
}

function login(user,pw) {
	console.log("send login");
	if(con == null){
		return;
	}
	var cmd_data = { "cmd":"login", "login":user, "client_pw":pw};
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
}

function set_detection(user,area,on_off){
	if(con == null) {
		return;
	}
	var cmd_data = { "cmd":"set_override", "rule":on_off, "area":area, "duration":"50"};
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