var con = null;
var f_t= 0;
var c_t=0;


$(function(){
	open_ws();
});


function open_ws() {
	//con = new WebSocket('wss://192.168.1.80:9879/');
	con = new WebSocket('wss://172.12.213.117:10823/');
	con.onopen = function(){
		console.log("onOpen");
		login("browser","hui");
	};

	// reacting on incoming messages
	con.onmessage = function(msg) {
		console.log("Message");
		console.log(msg);
		msg_dec=JSON.parse(msg.data);
		parse_msg(msg_dec);
	};
	con.onclose = function(){
		console.log("onClose");
	};
};



function parse_msg(msg_dec){
	// console.log(msg_dec);
	if(msg_dec["cmd"]=="m2v_login"){
		console.log("m2v_lgogin detected");
		check_append_m2m(msg_dec);
		update_hb(msg_dec["mid"],msg_dec["last_seen"]);
		update_state(msg_dec["account"],msg_dec["area"],msg_dec["mid"],msg_dec["state"],msg_dec["detection"]);
	}

	else if(msg_dec["cmd"]=="hb_m2m"){
		update_hb(msg_dec["mid"],msg_dec["last_seen"]);
	}

	else if(msg_dec["cmd"]=="state_change"){
		update_state(msg_dec["account"],msg_dec["area"],msg_dec["mid"],msg_dec["state"],msg_dec["detection"]);
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

		img=$("#"+msg_dec["mid"]+"_liveview_pic");
		if(img.length){
			if(msg_dec["img"]!=""){
				img.attr("src","data:image/jpeg;base64,"+msg_dec["img"]);
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
				update_state(msg_dec["account"],msg_dec["area"],msg_dec["mid"],-1,msg_dec["detection"]);
			}
		}
	}

	else if(msg_dec["cmd"]=="get_open_alert_ids"){
		var ids=msg_dec["ids"];
		var mid=msg_dec["mid"];
		console.log(ids);
		// here alarm view leeren
		console.log("leere alarm section for "+mid);
		var view=$("#"+mid+"_alarms");
		if(!view.length){
			alert(mid+"_alarms nicht gefunden");
		};
		view.html("");

		// add per element one line
		for(var i=0;i<ids.length;i++){		
			var alert=$("<div></div>");
			alert.attr({
				"id":"alert_"+mid+"_"+ids[i]
			});

			var txt=$("<div></div>");
			txt.attr({
				"id":"alert_"+mid+"_"+ids[i]+"_txt"
			});
			txt.html("Loading ...<br>");

			alert.append(txt);
			view.append(alert);

			var img=$("<img></img>");
			img.attr({
				"src" : "http://www.asus.com/support/images/support-loading.gif",
				"id":"alert_"+mid+"_"+ids[i]+"_img",
				"width":32,
				"height":32,

			});
			alert.append(img);
		};

		// request details	
		for(var i=0;i<ids.length;i++){
			var cmd_data = { "cmd":"get_alarm_details", "id":ids[i], "mid":mid};
			console.log(JSON.stringify(cmd_data));
			con.send(JSON.stringify(cmd_data));
		};
	}

	else if(msg_dec["cmd"]=="get_alarm_details"){
		var img=msg_dec["img"];
		var mid=msg_dec["mid"];
		// fill element with details
		// add new placeholder image
		var view=$("#alert_"+mid+"_"+msg_dec["id"]+"_txt");
		if(!view.length){
			console.log("get_alarm_details view not found");
		}
		var a = new Date(parseFloat(msg_dec["f_ts"])*1000);
		var min = a.getMinutes() < 10 ? '0' + a.getMinutes() : a.getMinutes();
		var hour = a.getHours();
		
		view.text("Movement detected at: "+a.getDate()+"."+(a.getMonth()+1)+"."+a.getFullYear()+" "+hour+":"+min);		

		var pic=$("#alert_"+mid+"_"+msg_dec["id"]+"_img");

		if(img.length>0){
			pic.attr({
				"id":img[0]["path"]
			});
			console.log("setze id: "+img[0]["path"]);


			for(var i=0;i<img.length && i<1;i++){
				var path=img[i]["path"];
				console.log("requesting image:"+path);
	
				var cmd_data = { "cmd":"get_img", "path":path};
				//console.log(JSON.stringify(cmd_data));
				con.send(JSON.stringify(cmd_data));
			};
		}
	}

	else if(msg_dec["cmd"]=="recv_req_file"){
		//console.log(msg_dec);
		var img=$(document.getElementById(msg_dec["path"])); // required as path contains dot
		if(img.length){
			console.log("bild gefunden");
		}else {
			console.log("nicht gefunden");
		};
		img.attr({
			"src":"data:image/jpeg;base64,"+msg_dec["img"],
			"width":228,
			"height":128
		});
	};
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

		text=$("<div></div>").text("--");
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

		var scroller=$("<div></div>");
		scroller.append(createRainbowDiv(100));
		scroller.css("width","500px").css("height","20px");
		lightcontrol.append(scroller);

		scroller=$("<div></div>");
		scroller.attr("id","colorslider_"+msg_dec["mid"]);
		scroller.css("clear","left");
		scroller.css("width","500px");
		scroller.slider({min:0, max:255, value:msg_dec["color_pos"], 
			slide:function(){
				var msg_int=msg_dec;
				return function(){
					refreshSwatch(msg_int["mid"]);
				};
			}(), 
			change:function(){
				var msg_int=msg_dec;
				return function(){
					refreshSwatch(msg_int["mid"]);
				};
			}()});
		lightcontrol.append(scroller);

		scroller=$("<div></div>");
		scroller.append(createRainbowDiv(0));
		scroller.css("width","500px").css("height","20px");
		lightcontrol.append(scroller);

		scroller=$("<div></div>");
		scroller.attr("id","brightnessslider_"+msg_dec["mid"]);
		scroller.css("clear","left");
		scroller.css("width","500px");
		scroller.slider({min:0, max:255, value:msg_dec["brightness_pos"], 
			slide:function(){
				var msg_int=msg_dec;
				return function(){
					refreshSwatch(msg_int["mid"]);
				};
			}(), 
			change:function(){
				var msg_int=msg_dec;
				return function(){
					refreshSwatch(msg_int["mid"]);
				};
			}()});
		lightcontrol.append(scroller);

		////////////////// COLOR SLIDER ////////////////////////////

		////////////////// ALARM MANAGER ////////////////////////////
		alarms=$("<div></div>").text("this is the alarms");
		alarms.attr({
			"id" : msg_dec["mid"]+"_alarms",
		});
		alarms.hide();
		node.append(alarms);
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
		set_interval(mid,0);
		view.delay(1000).fadeOut("fast");
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
		show_lightcontrol(mid);
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
		show_alarms(mid);
		get_open_alarms(mid);
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

function get_open_alarms(mid){
	if(con == null){
		return;
	}
	var cmd_data = { "cmd":"get_open_alert_ids","mid":mid};
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
};	


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
				}, 1000);
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

function createRainbowDiv(s){
	var gradient = $("<div>").css({display:"flex", height:"100%"});
	if(s>0){
		for (var i = 0; i<=255; i++){
			gradient.append($("<div>").css({"background-color":'hsl('+i+','+s+'%,50%)',flex:1}));
		}
	} else {
		for (var i = 0; i<=255; i++){
			gradient.append($("<div>").css({"background-color":'rgb('+i+','+i+','+i+')',flex:1}));
		}
	}
	return gradient;
}

function refreshSwatch(mid) {
	var c=($("<a>").css({"background-color":'hsl('+$( "#colorslider_"+mid ).slider( "value" )+',100%,50%)'})).css("background-color");
	var rgb = c.replace(/^(rgb|rgba)\(/,'').replace(/\)$/,'').replace(/\s/g,'').split(',');
	if($.isNumeric(rgb[0])){
		var color=$("#colorslider_"+mid).slider( "value" );
		var brightness=$("#brightnessslider_"+mid).slider( "value" );
		var mul=brightness/255;

		var cmd_data = { 
				"cmd":"set_color", 
				"r":parseInt(rgb[0]*mul), 
				"g":parseInt(rgb[1]*mul),
				"b":parseInt(rgb[2]*mul),
				"brightness_pos":brightness,
				"color_pos":color,
				"mid":mid};
		con.send(JSON.stringify(cmd_data));
	}
}

function update_hb(mid,ts){
	console.log("looking for hb field");
	if($("#"+mid+"_lastseen").length){
		console.log("ffound ");
		var a = new Date(parseFloat(ts)*1000);
		var min = a.getMinutes() < 10 ? '0' + a.getMinutes() : a.getMinutes(); 
		var hour = a.getHours();

		var delay=(Date.now()-(1000*parseFloat(ts)))/1000;
		var text = "Last Ping "+hour+":"+min+" - delay "+delay+" sec";
		$("#"+mid+"_lastseen").text(text);
		console.log("hb ts updated");
	}
}

function update_state(account,area,mid,state,detection){
	console.log("running update state on "+mid+"/"+state);
	e=$("#"+mid+"_state");
	if(e.length){
		e.text(state2str(state)+" || "+det2str(detection));
	}
	
	e=$("#"+account+"_"+area+"_status");
	if(e.length){
		e.text(det2str(detection));
	}
}
