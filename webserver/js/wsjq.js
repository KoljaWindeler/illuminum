// connection
var con = null;
//var IP="52.24.157.229";
//var IP="illuminum.speedoino.de";
var IP="illuminum.de";
var host="https://"+IP+"/";
var prelogin="";
var fast_reconnect=0;

// debug
var f_t= 0;
var c_t=0;

// cordova helper
var c_freeze_state=0;
var g_user="";//"browser";
var g_pw="";//"hui";

// big picture info
var g_areas=[];
var g_m2m=[];
var g_rules=[];
var g_logins=[];
var g_version=[];

// run as son as everything is loaded
$(function(){
	$('head').append('<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons" type="text/css" />');
	
	c_set_callback();
	var l=$("<div></div>");
	l.addClass("center_hor").addClass("center").attr("id","welcome_loading");
	l.insertAfter("#clients");
	l.append(get_loading("wli","Connecting..."));
	
	open_ws();
	//var txt=$("<div></div>");
	//txt.html("-->"+$(window).width()+"/"+$(window).height()+"<--");
	//$("#clients").append(txt);	
});


// triggered by the ondocument_ready
function open_ws() {
	console.log("connecting to the server");
	con = new WebSocket('wss://'+IP+':9879/');
	con.onopen = function(){
		while($("#rl_msg").length){
			$.fancybox.close();							
			$("#rl_msg").remove();
		};

		console.log("onOpen");
		request_pre_login();
	};

	// reacting on incoming messages
	con.onmessage = function(msg) {
		console.log(msg);
		msg_dec=JSON.parse(msg.data);
		parse_msg(msg_dec);
	};
	con.onclose = function(){
		console.log("onClose");
		// removed old existing entries
		while($("#rl_msg").length){
			$.fancybox.close();							
			$("#rl_msg").remove();
		};

		// remove register box .. sorry
		while($("#register_input_box").length){
			$.fancybox.close();
                        $("#register_input_box").remove();
                };

		// show fancybox
		show_fancybox("reconnecting...","rl_msg");

		if(c_freeze_state!=1){
			console.log("running reconnect in 2 sec");
			var timeout=2000;
			if(fast_reconnect){
				fast_reconnect=0;
				timeout=0;
			};
			setTimeout(function(){ open_ws();} , timeout);
		} else {
			console.log("will not run reconnect, as cordoba put us to sleep");
		};
	};
};


// on message will call this function
function parse_msg(msg_dec){
	var mid=msg_dec["mid"];

	// receive requested prelogin phrase
	if(msg_dec["cmd"]=="prelogin"){
		// store result in variable and continue with the login
		prelogin=msg_dec["challange"];
		check_login_data(1); 
	}

	// wrong login response
	else if(msg_dec["cmd"]=="login"){
		if(msg_dec["ok"]!="1"){
			console.log("received LOGIN-reject");
			g_user="nongoodlogin";
			g_pw="nongoodlogin";
			add_login("login failed");
		} else {
			add_menu();
			setTimeout("$('#wli').addClass('loginok')",1000);
			setTimeout("$('#wli').html('Login accepted, all your cameras will show up.<br>You can also register new cameras now.')",1000);
			g_version["v_short"]=msg_dec["v_short"];
			g_version["v_hash"]=msg_dec["v_hash"];
		};
		c_set_login(g_user,g_pw);
	}

	// server has established a connection between m2m and WS, this should be received after a login
	else if(msg_dec["cmd"]=="m2v_login"){
		//console.log("m2v_lgogin detected:"+msg_dec);

		// check if m2m is already visible, if not append it. Then update the state and timestamp
		check_append_m2m(msg_dec);
		update_hb(mid,msg_dec["last_seen"]);
		update_state(msg_dec["account"],msg_dec["area"],mid,msg_dec["state"],msg_dec["detection"],msg_dec["rm"],msg_dec["alarm_ws"]);
		// do it again here, to update a m2m that was existing (reconnect situation)
		set_alert_button_state($("#"+mid+"_alarm_counter"),$("#"+mid+"_toggle_alarms"),$("#"+mid+"_toggle_alarms_text"),msg_dec["open_alarms"]);
		set_override_buttons(msg_dec["account"],msg_dec["area"],msg_dec["rm_override"]);

		// remove loading if still existing and scroll down to the box 
		if($("#welcome_loading").length){
			$("#dummy").remove();
			$("#welcome_loading").remove();
			/*$('html,body').animate({
				scrollTop: $("#clients").offset().top-($(window).height()/20)
			},1000);*/
		};

		// restart camera if it was open before reconnect
		if(is_liveview_open(mid)){
			hide_liveview(mid,false);
			show_liveview(mid);
		};
	}

	// update the timestamp, we should receive this every once in a while
	else if(msg_dec["cmd"]=="hb_m2m"){
		update_hb(mid,msg_dec["last_seen"]);
	}

	// update the state, we only receive that if a box changes its state. E.g. to alarm or to disarm
	else if(msg_dec["cmd"]=="state_change"){
		update_state(msg_dec["account"],msg_dec["area"],mid,msg_dec["state"],msg_dec["detection"],msg_dec["rm"],msg_dec["alarm_ws"]);
	}

	// show a picture, we'll receive this because we requested it. Alarm will not send us pictures directly
	// this is a little different than the "requested_file" because we can't know the filename up front
	else if(msg_dec["cmd"]=="rf"){
		show_liveview_img(msg_dec);
	}

	// an m2m unit disconnects
	else if(msg_dec["cmd"]=="disconnect"){
		update_state(msg_dec["account"],msg_dec["area"],mid,-1,msg_dec["detection"],"",0);
	}

	// we'll request the alerts by sending "get_alert_ids" and the server will responde with this dataset below
	else if(msg_dec["cmd"]=="get_alert_ids"){
		parse_alert_ids(msg_dec["ids_open"],msg_dec["ids_closed"],msg_dec["open_max"],msg_dec["closed_max"],mid);
	}

	// every id that has been received by the dataset above will trigger a "get_alam_details" msg to the server, this handles the response
	else if(msg_dec["cmd"]=="get_alarm_details"){
		add_alert_details(msg_dec);
	}

	// display files that we've requested
	else if(msg_dec["cmd"]=="recv_req_file"){
		//console.log(msg_dec);
		var img=$(document.getElementById(msg_dec["path"])); // required as path may contains dot
		if(img.length){
			img.attr({
				"src"	: "data:image/jpeg;base64,"+msg_dec["img"],
				"id"	: "set_"+msg_dec["path"],
				"width"	: msg_dec["width"],
				"height": msg_dec["height"]
			});
		}else {
			console.log("nicht gefunden");
		};

	}

	// update "sendmail" button
	else if(msg_dec["cmd"]=="send_alert"){
		var send_button=$("#alert_"+msg_dec["mid"]+"_"+msg_dec["aid"]+"_send");
		if(parseInt(msg_dec["status"])==1){
			send_button.text("eMail send!").fadeIn();
		} else {
			send_button.text("eMail error!").fadeIn();
		};
	}

	// updated count of alerts, show correct button style and maybe close the popup
	else if(msg_dec["cmd"]=="update_open_alerts"){
		var button=$("#"+mid+"_toggle_alarms");
		var txt=$("#"+mid+"_toggle_alarms_text");
		var counter=$("#"+mid+"_alarm_counter");
		set_alert_button_state(counter,button,txt,msg_dec["open_alarms"]);

		// close msg about open alarms if someone already acknowledged them
		if($("#"+mid+"_old_alerts").length && msg_dec["open_alarms"]==0){
			event.stopPropagation();
			$.fancybox.close();				
		}
	}

	// update menu timestamp if we are part of the fast heartbeat
	else if(msg_dec["cmd"]=="hb_fast"){
		var t=$("#HB_fast");
		if(msg_dec["time"]!="" && msg_dec["tasks"]!=""){
			t.html("Server:<br>"+msg_dec["time"]+"<br>"+msg_dec["tasks"]);
		};
	}

	// received callback from register
	else if(msg_dec["cmd"]=="new_register"){
		callback_register(msg_dec["status"]);
	}

	// set override buttons
	else if(msg_dec["cmd"]=="set_override"){
		if(msg_dec["ok"]==1){
			set_override_buttons(msg_dec["account"],msg_dec["area"],msg_dec["rm_override"]);
		};
	}

	// parse incoming areas for sidebar
	else if(msg_dec["cmd"]=="get_areas"){
		parse_sidebar_info(msg_dec);
	}

	// parse incoming cams for sidebar
	else if(msg_dec["cmd"]=="get_cams"){
		parse_sidebar_info(msg_dec);
	}

	// parse incoming rules for sidebar
	else if(msg_dec["cmd"]=="get_logins"){
		parse_sidebar_info(msg_dec);
	}

	// parse incoming rules for sidebar
	else if(msg_dec["cmd"]=="get_rules"){
		parse_sidebar_info(msg_dec);
	}

	// response from server
	else if(msg_dec["cmd"]=="update_login"){
		$.fancybox.close();				

		if(msg_dec["ok"]=="0"){
			login_entry_button_state(msg_dec["id"],"show");
			request_all_logins();
		} else if(msg_dec["ok"]=="-2") {
			alert("this username was already taken, choose another one");
		}
	};


}

/////////////////////// END OF PARSE MESSAGE ////////////////////////

/////////////////////////7///////////////// SHOW LIVEVIEW IMAGES //////////////////////////////////////////
// triggered by: parse_msg
// arguemnts:	 complete websocket msg, as multiple arguemnts are required
// what it does: set mid_liveview attr to incoming picture, reset countdown
// why: 	 to display the incoming pictures
/////////////////////////7///////////////// SHOW LIVEVIEW IMAGES //////////////////////////////////////////

function show_liveview_img(msg_dec){
	// hide loading dialog, if there is one
	var txt=$("#"+msg_dec["mid"]+"_liveview_txt");
	if(txt.length){
		txt.hide();
	};

	// show debug speed
	if(msg_dec["up_down_debug"]!=""){
		txt=$("#"+msg_dec["mid"]+"_liveview_up_down_debug");
		if(txt.length){
			txt.show();
		}
		txt.text(msg_dec["up_down_debug"]);
	};

	// display picture
	var img=$("#"+msg_dec["mid"]+"_liveview_pic");
	if(img.length){
		//console.log("mid_img: #"+msg_dec["mid"]+"_liveview_pic gefunden!!");

		if(msg_dec["img"]!=""){
			// if we receive the first image, scroll to it
			if(img.attr("src")==host+"images/support-loading.gif"){
			$('html,body').animate({
					scrollTop: img.offset().top-($(window).height()/20)
				},1000);
			};

			// display image
			resize_alert_pic(msg_dec["mid"],msg_dec["img"]);
		};
	} else {
		console.log("konnte mid_img: #"+msg_dec["mid"]+"_liveview_pic nicht finden!!");
	};

	// handle countdown
	if(msg_dec["webcam_countdown"]<10){
		var cmd_data = { "cmd":"reset_webcam_countdown"};
		//console.log(JSON.stringify(cmd_data));
		con.send(JSON.stringify(cmd_data)); 		
	}
};

/////////////////////////7///////////////// PARSE ALERT IDS //////////////////////////////////////////
// triggered by: open_alerts -> msg to server,response -> parse_msg -> this
// arguemnts:	 list of alert ids and MID 
// what it does: remove loading, call add_alert() AND request alert_details for each ID in ids
// why: 	 to prepare alert view for incoming pictures
/////////////////////////7///////////////// PARSE ALERT IDS //////////////////////////////////////////

function parse_alert_ids(ids_open,ids_closed,open_max,closed_max,mid){
	// remove loading it and add a ack all button
	var closed_disp=$("#"+mid+"_alarms_closed_display");
	var open_disp=$("#"+mid+"_alarms_open_display");

	var closed_stopper=$("#"+mid+"_alarms_closed_stopper");
	var open_stopper=$("#"+mid+"_alarms_open_stopper");

	var ids_open_old=$("#"+mid+"_alarms_open_list").text().split(",");
	for(j=0;j<ids_open_old.length; j++){
		ids_open_old[j]=parseInt(ids_open_old[j]);
	};

	var ids_closed_old=$("#"+mid+"_alarms_closed_list").text().split(",");
	for(j=0;j<ids_closed_old.length; j++){
		ids_closed_old[j]=parseInt(ids_closed_old[j]);
	};

	var closed_navi=$("#"+mid+"_alarms_closed_navigation");
	var open_navi=$("#"+mid+"_alarms_open_navigation");

	// store limits and current list
	$("#"+mid+"_alarms_closed_list").text(ids_closed);
	$("#"+mid+"_alarms_closed_max").text(closed_max);
	$("#"+mid+"_alarms_open_list").text(ids_open);
	$("#"+mid+"_alarms_open_max").text(open_max);

	// generate links
	var field_start= ["#"+mid+"_alarms_open_start", "#"+mid+"_alarms_closed_start"];
	var field_end=	 ["#"+mid+"_alarms_open_count",	"#"+mid+"_alarms_closed_count"];
	var max=	 [open_max,			closed_max];
	var disp=	 [open_disp,			closed_disp];
	var stopper=	 [open_stopper,			closed_stopper];
	var ids=	 [ids_open,			ids_closed];
	var old_ids=	 [ids_open_old,			ids_closed_old];
	var navigation=  [open_navi,			closed_navi];

	for(i=0; i<2; i++){
		// new ids that we should add
		var mod_front=[];
		var mod_back=[];

		// check if we still have the exact same content in old and current id list
		var same_content=true;
		if(old_ids.length==ids.length){
			if(ids.length==0){
				same_content=false;
			} else {
				for(j=0; j<old_ids[i].length; j++){
					if(old_ids[i][j]!=ids[i][j]){
						same_content=false;
					};
				};
			};
		};

		$("#loading_window").remove();
		if(same_content){
			continue;
		} else {
			// check if it is nearly the same, just one new entry up front, or one missing that we might have acknowledged
			//console.log("ids_old="+old_ids[i]);
			//console.log("ids_new="+ids[i]);
			//console.log("length="+ids[i].length);

			// check if we have to add some id's
			var found_old=0;
			for(j=0; j<ids[i].length; j++){
				if($.inArray(ids[i][j],old_ids[i])==-1){
					if(found_old){
						mod_back.push(ids[i][j]);
					} else {
						mod_front.push(ids[i][j]);	
					};
				} else {
					found_old=1;
				}
			};

			// check if we have to remove some id's
			for(j=0; j<old_ids[i].length; j++){
				if($.inArray(old_ids[i][j],ids[i])==-1){
					mod_back.push(-1*old_ids[i][j]); // it doesn't matter which mod_ we use, as long as we erase
				}
			};
		}

		var start=parseInt($(field_start[i]).text())+1;
		var end=start+parseInt($(field_end[i]).text())-1;

		// generate valid links
		if(end>max[i]){ end=max[i]; };
		if(start>end) { start=end; };
		var link=$("<div></div>").text(start+" - "+end+" ( Total: "+max[i]+")").attr("id","alert_"+mid+"_"+i+"_fromto");
		link.addClass("inline_block");

		var prev=$("<img></img>").attr("id","alert_"+mid+"_"+i+"_prev");
		if(start>1){
			prev.click(function(){
				var mid_int=mid;
				var start_int=start;
				var field_start_int=field_start[i];
				return function(){
					$(field_start_int).text(Math.max(start_int-10-1,0));
					get_alarms(mid_int);
				};					
			}());
			prev.addClass("alert_navigation_prev");
		} else {
			prev.addClass("alert_navigation_prev_deactivated");
		}

		var next=$("<img></img>").attr("id","alert_"+mid+"_"+i+"_next");
		if(end<max[i]){
			next.click(function(){
				var mid_int=mid;
				var start_int=start;
				var field_start_int=field_start[i];
				return function(){
					$(field_start_int).text(start_int+10-1);
					get_alarms(mid_int);
				};					
			}());
			next.addClass("alert_navigation_next");
		} else {
			next.addClass("alert_navigation_next_deactivated");
		}
		// end of link generation
		navigation[i].text("");
		navigation[i].append(prev);
		navigation[i].append(link);
		navigation[i].append(next);
	

		// show button or message alarm 
		if(ids[i].length && i==0){
			$("#alert_"+mid+"_"+i+"_no_alert_msg").remove();
			if($("#alert_"+mid+"_"+i+"_ack_all").length==0){
				// add ack all button
				var ack=$("<a></a>");
				ack.attr({
					"id":"alert_"+mid+"_"+i+"_ack_all",
					"class":"button"
				});
				ack.text("Acknowledge all alert");
				ack.click(function(){
					var mid_int=mid;
					return function(){
						ack_all_alert(mid_int);
					};
				}());
				disp[i].append(ack);
			}
		} else if(ids[i].length==0){
			$("#alert_"+mid+"_"+i+"_ack_all").remove();
			if($("#alert_"+mid+"_"+i+"_no_alert_msg").length==0){
				// show a "huray, no alert"
				var txt=$("<div></div>").attr("id","alert_"+mid+"_"+i+"_no_alert_msg");
				txt.text("horay, no alarms");
				txt.addClass("center");
				txt.addClass("clear_both");
				disp[i].append(txt);
			};
		}

		
		for(j=mod_front.length - 1; j>= 0; j--){
			if(mod_front[j]>0){
				// insert a helper to reroute the anchor for 'add_alert()'
				var alert_helper=$("<div></div>");
				alert_helper.attr({
					"id":"alert_helper_"+mid+"_"+mod_front[j],
				});
				alert_helper.insertBefore(stopper[i]);
				add_alert(mod_front[j],mid,alert_helper);
	
				// move the stopper forwards
				stopper[i].detach();
				stopper[i].insertBefore(alert_helper);
			};
		};

		for(j=mod_back.length - 1; j>= 0; j--){
			if(mod_back[j]>0){
				add_alert(mod_back[j],mid,disp[i]);
			};				
		};

		for(j=0;j<mod_front.length; j++){
			if(mod_front[j]<0){
				var o=$("#alert_helper_"+mid+"_"+(-1*mod_front[j]));
				if(o.length){
					o.remove();
				}
				var o=$("#alert_"+mid+"_"+(-1*mod_front[j]));
				if(o.length){
					o.remove();
				}
			} else if(mod_front[j]>0) {
				// request details	
				var cmd_data = { "cmd":"get_alarm_details", "id":mod_front[j], "mid":mid};
				console.log(JSON.stringify(cmd_data));
				con.send(JSON.stringify(cmd_data)); 
			};
		};
		for(j=0;j<mod_back.length; j++){
			if(mod_back[j]<0){
				var o=$("#alert_helper_"+mid+"_"+(-1*mod_back[j]));
				if(o.length){
					o.remove();
				}
				var o=$("#alert_"+mid+"_"+(-1*mod_back[j]));
				if(o.length){
					o.remove();
				}
			} else if(mod_back[j]>0){
				// request details	
				var cmd_data = { "cmd":"get_alarm_details", "id":mod_back[j], "mid":mid};
				console.log(JSON.stringify(cmd_data));
				con.send(JSON.stringify(cmd_data)); 
			};
		};
	};
};

/////////////////////////////////////////// ADD ALERT //////////////////////////////////////////
// triggered by: open_alerts -> msg to server,response -> parse_msg -> parse_alert_ids() -> this
// arguemnts:	 alert id, root view id and MID 
// what it does: adds a preliminary and "empty" alert element to the alarm view, loading image, timestamp, ...
// why: 	 to prepare the alert view for details, requested by parse_alert_ids()
/////////////////////////////////////////// ADD ALERT //////////////////////////////////////////

function add_alert(aid,mid,view){
	// if m2m lable ist 123456789 and alarm is 1010 then we should get this:
	// <div id="alert_123456789_1010">
	// 	<img id="alert_123456789_1010_img"> -> id changes to set_alert_123456789_1010_img</img>
	//	<div id="alert_123456789_101_side>
	//	 	<div id="alert_123456789_1010_txt">Loading -> Movement detected at: 8.6.2015 21:51</div>
	//		<a id="alert_123456789_1010_ack">button></a>
	//	</div>
	//	<div id="alert_123456789_1010_slider">
	//		<ul...><li></li></ul>
	//	</div>
	// </div>
			
	// root 
	var alert=$("<div></div>");
	alert.attr({
		"id":"alert_"+mid+"_"+aid,
	});
	alert.addClass("inline_block");
	view.append(alert);

	// img container
	var img_container=$("<div></div>");
	var width=$("#"+mid+"_alarms").width()*0.5; // 50% of the width of the alert box
	img_container.attr({
		"style":"width: "+width+"px; "+
		"height:"+(width/1280*720+20)+"px;"
	});
	img_container.addClass("float_left");
	alert.append(img_container);

	// preview image
	var img=$("<img></img>");
	img.attr({
		"src" : host+"images/support-loading.gif",
		"id":"alert_"+mid+"_"+aid+"_img",
		"width":32,
		"height":32
	});
	img.addClass("alert_preview");
	img.addClass("center");
	img_container.append(img);

	// side block
	var side=$("<div></div>");
	side.attr("id","alert_"+mid+"_"+aid+"_side");	
	side.addClass("alert_side");
	alert.append(side);

	// text field
	var txt=$("<div></div>");
	txt.attr({
		"id":"alert_"+mid+"_"+aid+"_date"
	});
	txt.html("Loading ...");
	side.append(txt);

	// status button
	var status=$("<a></a>");
	status.attr({
		"id":"alert_"+mid+"_"+aid+"_status",
		"style":"cursor:pointer",
	});
	status.addClass("m2m_text");
	status.text("System Status");
	status.hide();
	side.append(status);

	// ack status
	txt=$("<div></div>");
	txt.attr({
		"id":"alert_"+mid+"_"+aid+"_ack_status"
	});
	txt.html("Loading ...");
	txt.hide();
	side.append(txt);


	// ack button
	var ack=$("<a></a>");
	ack.attr({
		"id":"alert_"+mid+"_"+aid+"_ack",
		"class":"button"
	});
	ack.text("Acknowledge alert");
	ack.click(function(){
		var id_int=aid;
		var mid_int=mid;
		return function(){
			ack_alert(id_int,mid_int);
			get_alarms(mid_int);
		};
	}());
	ack.hide();
	side.append(ack);

	// del button
	var del=$("<a></a>");
	del.attr({
		"id":"alert_"+mid+"_"+aid+"_del",
		"class":"button"
	});
	del.text("Delete alert");
	del.click(function(){
		var id_int=aid;
		var mid_int=mid;
		return function(){
			del_alert(id_int,mid_int);
			get_alarms(mid_int);
		};
	}());
	del.hide();
	side.append(del);

	// send button
	var send=$("<a></a>");
	send.attr({
		"id":"alert_"+mid+"_"+aid+"_send",
		"class":"button"
	});
	send.text("eMail pictures");
	send.click(function(){
		var id_int=aid;
		var mid_int=mid;
		return function(){
			send_alert(id_int,mid_int);
		};
	}());
	send.hide();
	side.append(send);

	// slider
	var slider=$("<div></div>");
	slider.attr({
		"id":"alert_"+mid+"_"+aid+"_slider"
	});
	slider.hide();
	alert.append(slider);
};

/////////////////////////////////////////// ADD ALERT DETAILS //////////////////////////////////////////
// triggered by: open_alerts -> msg to server,response -> parse_msg() -> parse_alert_ids() -> msg to server -> parse_msg() -> this
// arguemnts:	 full msg as multple arguments are required
// what it does: fills the preliminary alert with data, img, activates buttons
// why: 	 finalize the alertview
/////////////////////////////////////////// ADD ALERT DETAILS //////////////////////////////////////////

function add_alert_details(msg_dec){
	var img=msg_dec["img"];
	var mid=msg_dec["mid"];
	var rm=msg_dec["rm_string"];
	// fill element with details

	// show text info
	var date_txt=$("#alert_"+mid+"_"+msg_dec["id"]+"_date");
	if(!date_txt.length){
		console.log("get_alarm_details view not found");
	} else {
		var a = new Date(parseFloat(msg_dec["f_ts"])*1000);
		var min = a.getMinutes() < 10 ? '0' + a.getMinutes() : a.getMinutes();
		var hour = a.getHours();
		date_txt.text(""+a.getDate()+"."+(a.getMonth()+1)+"."+a.getFullYear()+" "+hour+":"+min);
		date_txt.addClass("m2m_text");
	}		

	// show status button
	var status_button=$("#alert_"+mid+"_"+msg_dec["id"]+"_status");
	status_button.click(function(){
		var txt=rm;
		return function(){
			txt2fb(format_rm_status(txt));
		};
	}());
	status_button.show();

	// show ack status
	var ack_status=$("#alert_"+mid+"_"+msg_dec["id"]+"_ack_status");
	if(msg_dec["ack"]==0){
		ack_status.text("Not acknowledged");
	} else {
		var a = new Date(parseFloat(msg_dec["ack_ts"])*1000);
		var min = a.getMinutes() < 10 ? '0' + a.getMinutes() : a.getMinutes();
		var hour = a.getHours();
		ack_status.html("Checked by '"+msg_dec["ack_by"]+"'<br> at "+hour+":"+min+" "+a.getDate()+"."+(a.getMonth()+1)+"."+a.getFullYear());
	};
	ack_status.addClass("m2m_text");
	ack_status.show();

	// show ack button
	if(msg_dec["ack"]==0){
		var ack_button=$("#alert_"+mid+"_"+msg_dec["id"]+"_ack");
		ack_button.show();
	};

	// show del button
	if(msg_dec["ack"]!=0){
		var del_button=$("#alert_"+mid+"_"+msg_dec["id"]+"_del");
		del_button.show();
	};

	// show send button
	var send_button=$("#alert_"+mid+"_"+msg_dec["id"]+"_send");
	send_button.show();
	

	// add new placeholder image
	if(img.length>0){
		// this is picture nr 1 the title picture
		var pic=$("#alert_"+mid+"_"+msg_dec["id"]+"_img");		
		pic.attr({
			"id":img[0]["path"],
			"style":"cursor:pointer"
		});
		pic.click(function(){
			var img_int=img; 								// list of all pictures for this alarm
			var mid_int=mid;	 							// mid for this alarm
			var slider_id="#alert_"+mid_int+"_"+msg_dec["id"]+"_slider";			// id for the div in which the slider should
			var core_int=img[0]["path"].substr(0,img[0]["path"].indexOf("."));		// slider itself must have an unique id without "."
			return function(){
				var slider=$(slider_id);
				slider.text("");
				slider.show();
				show_pic_slider(img_int,mid_int,core_int,slider_id);
			}
		}());
		
		// request picture from server
		var path=img[0]["path"];
		var width=$("#"+mid+"_alarms").width()*0.5; // 50% of the width of the alert box
		var cmd_data = { "cmd":"get_img", "path":path, "width":width, "height":width*720/1280};
		con.send(JSON.stringify(cmd_data));
	} // end of if img 
};



/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: user button
// arguemnts:	 id of the alert and MID
// what it does: sends a message to the server to ack the alert
// why: 	 to get ridge of the alert in the alert view
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function ack_alert(id,mid){
	// remove field
	$("#alert_"+mid+"_"+id).fadeOut(600, function() { $(this).remove(); });

	// decrement nr
	var button=$("#"+mid+"_toggle_alarms");
	var open_alarms=parseInt(button.text().substring(0,button.text().indexOf(" ")))-1;
	var txt=$("#"+mid+"_toggle_alarms_text");
	var counter=$("#"+mid+"_alarm_counter");
	set_alert_button_state(counter,button,txt,open_alarms);

	var cmd_data = { "cmd":"ack_alert", "mid":mid, "aid":id};
	//console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data)); 		
};

/////////////////////////////////////////// DEL ALERT //////////////////////////////////////////
// triggered by: user button
// arguemnts:	 id of the alert and MID
// what it does: sends a message to the server to ack the alert
// why: 	 to get ridge of the alert in the alert view
/////////////////////////////////////////// DEL ALERT //////////////////////////////////////////

function del_alert(id,mid){
	// remove field
	$("#alert_"+mid+"_"+id).fadeOut(600, function() { $(this).remove(); });

	var cmd_data = { "cmd":"del_alert", "mid":mid, "aid":id};
	//console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data)); 		
};

/////////////////////////////////////////// SEND ALERT //////////////////////////////////////////
// triggered by: user button
// arguemnts:	 id of the alert and MID
// what it does: sends a message to the server to generate a mail with the pictures
// why: 	 to get evidence if you need it
/////////////////////////////////////////// SEND ALERT //////////////////////////////////////////

function send_alert(id,mid){
	$("#alert_"+mid+"_"+id+"_send").text("eMail requested...");

	var cmd_data = { "cmd":"send_alert", "mid":mid, "aid":id};
	//console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data)); 		
};

/////////////////////////////////////////// ACK ALL ALERT //////////////////////////////////////////
// triggered by: user button
// arguemnts:	 MID
// what it does: sends a message to the server to ack all the alerts for this box
// why: 	 to get ridge of all alerts in the alert view at once
/////////////////////////////////////////// ACK ALL ALERT //////////////////////////////////////////

function ack_all_alert(mid){
	var cmd_data = { "cmd":"ack_all_alert", "mid":mid};
	con.send(JSON.stringify(cmd_data)); 		

	show_alarms(mid); 	// its already open, but this will reset the content
	get_alarms(mid);	// and this should send us an empty list
};


/////////////////////////////////////////// SHOW PIC SLIDER //////////////////////////////////////////
// triggered by: user click on first alert picture
// arguemnts:	 list of images(paths),MID, core=pseudo-id for all images in the slider, slider_id=anchor to put the images in
// what it does: calculates a best fit for a 70% windows size, genearte loadingimages and wrap a fancybox around, and request images
// why: 	 to have a fullscreen view of the alert pictures, they might be important
/////////////////////////////////////////// SHOW PIC SLIDER //////////////////////////////////////////

function show_pic_slider(img,mid,core,slider_id){
	// slider_id == id of the div in which we should place our content
	// core is the name for this slider

	var view = $(slider_id);
	view.html("");

	// get best Resolution, for pictures
	var w=$(window).width();
	var h=$(window).height();
	var scale=w/1280; // assume portait
	if(w/1280 > h/720){
		// e.g. 16:9 landscape 
		scale=h/720;
	}

	// create children and request them
	for(var i=0;i<img.length;i++){
		//console.log("appending:"+img[i]["path"]);
		var fb=$("<a></a>");				
		fb.attr({
			"rel":core,
			"title":(img.length-i)+"/"+(img.length),
		});
		
		var pic=$("<img></img>");
		pic.attr({
			"src" : host+"images/support-loading.gif",
			"id":img[i]["path"],
			"width":scale*0.7*1280,
			"height":scale*0.7*720,
		});
		
		fb.append(pic);
		view.append(fb);
		var cmd_data = { "cmd":"get_img", "path":img[i]["path"], "height":720*scale*0.7, "width":1280*scale*0.7};
		con.send(JSON.stringify(cmd_data));
		
		//console.log("send request for:path "+img[i]["path"]);
	}

	
	// fancybox the jQuery object is sorted, but the fancybox is not .. grmpf
	$("a[rel="+core+"]").fancybox({"openEffect":"elastic"}).trigger("click");
}

/////////////////////////////////////////// CHECK_APPEND_M2M //////////////////////////////////////////
// triggered by: parse_msg()
// arguemnts:	 complete msg
// what it does: create an area and a m2m if it does not exists if it exists, remove it
// why: 	 core code for the interface
/////////////////////////////////////////// CHECK_APPEND_M2M //////////////////////////////////////////
function check_append_m2m(msg_dec){
	//console.log(msg_dec);
	// get root clients node
	if($("#clients").length){
		var mid=msg_dec["mid"];
		var node=$("#"+mid);

		// check if this m2m already exists, if so remove it as it might be underthe wrong area
		if(node.length){
			var area=node.parent();
			// count nodeof class area_m2m on area if just one then we have to delete this area as well
			if(area.children('.area_m2m').length==1){
				area.remove();
			} else {
				node.remove();
			};
			/////////////////// REMOVE M2M ////////////////////////////(
		}

		// AREA Creation if needed
		var area=$("#"+msg_dec["account"]+"_"+msg_dec["area"]);
		//console.log("suche nach gruppe "+msg_dec["account"]+"_"+msg_dec["area"]);
		// check if area is already existing
		if(area.length==0){

			/////////////////// CREATE AREA ////////////////////////////(
			var node=$("<div></div>");
			node.attr({
				"id" : msg_dec["account"]+"_"+msg_dec["area"],
				"class": "area_node"
			});

			var header=$("<div></div>");
			header.attr({
				"id" : msg_dec["account"]+"_"+msg_dec["area"]+"_header",
				"class": "area_header"
			});
			node.append(header);

			var header_first_line=$("<div></div>");
			header_first_line.attr({
				"id" : msg_dec["account"]+"_"+msg_dec["area"]+"_header_first_line",
				"class": "area_header"
			});
			header.append(header_first_line);
			
			var icon=$("<img></img>");
			icon.attr({
				"id": msg_dec["account"]+"_"+msg_dec["area"]+"_icon",
				"class": "area_header"
			});
			icon.addClass("home_sym");
			header_first_line.append(icon);
	
			var header_text=$("<div></div>");
			header_text.attr({
				"class":"area_header_text"
			});
			header_first_line.append(header_text);

			var text=$("<div></div>").text(msg_dec["area"]);
			text.attr({
				"id" : msg_dec["account"]+"_"+msg_dec["area"]+"_title",
				"class": "area_header_title",
			});
			header_text.append(text);

			text=$("<div></div>");
			text.attr({
				"id" : msg_dec["account"]+"_"+msg_dec["area"]+"_status",
				"class": "area_header_status"
			});
			text.click(function(){
				var rm_int="all cameras in this area offline,<br>will load rules as soon as<br>a camera comes online";
				return function(){
					txt2fb(format_rm_status(rm_int));
				};
			}());
			header_text.append(text);

			var header_button=$("<div></div>");
			header_button.attr({
				"class":"area_header_button"
			});
			header.append(header_button);

			// three buttons now, on|auto|off
			var button=$("<a></a>");
			button.attr("id",msg_dec["account"]+"_"+msg_dec["area"]+"_on");
			button.text("on");
			button.addClass("button");
			button.addClass("button_deactivated");
			header_button.append(button);

			var button=$("<a></a>");
			button.attr("id",msg_dec["account"]+"_"+msg_dec["area"]+"_auto");
			button.text("auto");
			button.addClass("button");
			button.addClass("button_deactivated");
			header_button.append(button);

			var button=$("<a></a>");
			button.attr("id",msg_dec["account"]+"_"+msg_dec["area"]+"_off");
			button.text("off");
			button.addClass("button");
			button.addClass("button_deactivated");
			header_button.append(button);
			// three buttons now, on|auto|off

			$("#clients").append(node);
			area=node;
			/////////////////// CREATE AREA ////////////////////////////(
		} // area
	} // clients

	/////////////////// CREATE M2M ////////////////////////////(
	//console.log("knoten! nicht gefunden, lege ihn an");
	node=$("<div></div>");
	node.attr({
		"id":mid,
		"class":"area_m2m"
	});
	
	var m2m_header=$("<div></div>");
	m2m_header.attr({
		"id":mid+"_header",
		"class":"m2m_header"
	});
	node.append(m2m_header);
/*
	var icon=$("<img></img>");
	icon.attr({
		"id": mid+"_icon",
		"width": 64,
		"height": 51,
		"class":"m2m_header"
		});
	icon.addClass("cam_sym");
	m2m_header.append(icon);
*/

	var m2m_header_text=$("<div></div>");
	m2m_header_text.attr({
		"id":mid+"_header_text",
		"class":"m2m_header_text"
	});
	m2m_header.append(m2m_header_text);
	
	var text=$("<div></div>").text(msg_dec["alias"]);
	text.attr({
		"id" : mid+"_name",
		"class": "m2m_text_name"
	});
	m2m_header_text.append(text);
		
	var glow=$("<div></div>");
	glow.attr("id",mid+"_glow");
	glow.addClass("glow_dot"); // setting real state in update routine
	glow.addClass("float_left");
	//m2m_header_text.append(glow);
	

	text=$("<div></div>");
	text.attr({
		"id" : mid+"_state",
		"class": "m2m_text"
	});
	text.addClass("float_left");
	m2m_header_text.append(text);

	text=$("<div></div>").text("--");
	text.attr({
		"id" : mid+"_lastseen",
		"class": "m2m_text"
	});
	text.addClass("clear_both");
	//m2m_header_text.append(text);

	var m2m_header_button=$("<div></div>");
	m2m_header_button.attr({
		"class":"m2m_header_button"
	});
	node.append(m2m_header_button);

	//////////// live view button /////////////
	var wb=$("<div></div>");
	wb.addClass("inline_block");
	button=$("<a></a>");
	button.attr({
		"id": msg_dec["mid"]+"_toggle_liveview",
	});
	button.text("set_via_css");
	button.addClass("live_sym");
	button.click(function(){
		var msg_int=msg_dec;
		return function(){
			toggle_liveview(msg_int["mid"]);
		};
	}());
	set_button_state(button,msg_dec["state"]);
	wb.append(button);
	var wl=$("<div></div>");
	wl.attr("id",mid+"_toggle_liveview_text");
	wl.addClass("toggle_liveview_text");
	wl.addClass("toggle_text");
	wb.append(wl);
	m2m_header_button.append(wb);
	//m2m_header_button.append(button);
	//////////// live view button /////////////
		
	//////////// setup controll button /////////////
	wb=$("<div></div>");
	wb.addClass("inline_block");
	button=$("<a></a>");
	button.attr({
		"id": msg_dec["mid"]+"_toggle_setupcontrol",
	});
	button.addClass("color_sym");
	button.click(function(){
		var msg_int=msg_dec;
		return function(){
			toggle_setupcontrol(msg_int["mid"]);
		};
	}());
	button.text("set_via_css");
	set_button_state(button,msg_dec["state"]);
	wb.append(button);
	wl=$("<div></div>");
	wl.attr("id",mid+"_toggle_setupcontrol_text");
	wl.addClass("toggle_setupcontrol_text");
	wl.addClass("toggle_text");
	wb.append(wl);
	m2m_header_button.append(wb);
	//m2m_header_button.append(button);
	//////////// setup controll button /////////////

	//////////// alert button /////////////
	wb=$("<div></div>");
	wb.addClass("inline_block");
	wb.addClass("alarm_button");

	var num_text=$("<div></div>");
	num_text.text("4");
	num_text.addClass("alarm_sym_wrap");
	num_text.attr("id",msg_dec["mid"]+"_alarm_counter");
	num_text.click(function(){
		var msg_int=msg_dec;
		return function(){
			toggle_alarms(msg_int["mid"]);
		};
	}());
	wb.append(num_text);

	button=$("<a></a>");
	button.attr({
		"id": msg_dec["mid"]+"_toggle_alarms",
	});
	button.addClass("alarm_sym");
	button.click(function(){
		var msg_int=msg_dec;
		return function(){
			toggle_alarms(msg_int["mid"]);
		};
	}());
	button.text("no alarms");
	wb.append(button);

	wl=$("<div></div>");
	wl.attr("id",mid+"_toggle_alarms_text");
	wl.addClass("toggle_text");		// size etc
	wl.addClass("toggle_alarms_text");	// color and text
	wb.append(wl);
	m2m_header_button.append(wb);

	// hide it if no alarm is available
	set_alert_button_state(num_text,button,wl,msg_dec["open_alarms"]);
	//////////// alert button /////////////



	////////////////// LIVE VIEW ////////////////////////////
	liveview=$("<div></div>");
	liveview.attr({
		"id" : mid+"_liveview",
	});
	liveview.addClass("center");
	liveview.hide();
	node.append(liveview);

	var txt=$("<div></div>");
	txt.attr("id",mid+"_liveview_txt");
	txt.attr("style","padding-top:20px;");
	txt.html("Loading liveview<br>");
	liveview.append(txt);

	// upload download info
	txt=$("<div></div>");
	txt.attr("id",mid+"_liveview_up_down_debug");
	txt.attr("style","padding-top:20px;");
	txt.html("Loading speed info<br>");
	txt.addClass("tiny_text");
	txt.hide();
	liveview.append(txt);
	

	// fancybox link around the liveview
	var rl = $("<a></a>");
	rl.attr("href","#"+mid+"_liveview_pic");
	rl.fancybox({
		beforeShow: function() { 
			mid_i=mid; 
			resize_alert_pic(mid_i,""); 
		},
		afterClose: function() {	
			mid_i=mid;
              	    		$("#"+mid_i+"_liveview_pic").show();
			resize_alert_pic(mid,""); 
       		}
	});
	liveview.append(rl);

	var img=$("<img></img>");
	img.attr({
		"src" : host+"images/support-loading.gif",
		"id" : mid+"_liveview_pic",
		"width":64,
		"height":64
	});
	rl.append(img);
	////////////////// LIVE VIEW ////////////////////////////

	////////////////// COLOR SLIDER ////////////////////////////
	setupcontrol=$("<div></div>");
	setupcontrol.attr({
		"id" : mid+"_setupcontrol",
	});
	setupcontrol.hide();
	node.append(setupcontrol);

	var scroller=$("<div></div>");
	scroller.append(createRainbowDiv(100));
	scroller.addClass("setup_controll_color");
	setupcontrol.append(scroller);

	scroller=$("<div></div>");
	scroller.attr({
		"id":"colorslider_"+mid,
		"class":"setup_controll_scroller"
	});
	scroller.slider({min:0, max:255, value:msg_dec["color_pos"], 
		slide:function(){
			var msg_int=msg_dec;
			return function(){
				send_color(msg_int["mid"]);
			};
		}(), 
		change:function(){
			var msg_int=msg_dec;
			return function(){
				send_color(msg_int["mid"]);
			};
		}()});
	setupcontrol.append(scroller);

	scroller=$("<div></div>");
	scroller.append(createRainbowDiv(0));
	scroller.addClass("setup_controll_color");
	setupcontrol.append(scroller);

	scroller=$("<div></div>");
	scroller.attr({
		"id":"brightnessslider_"+mid,
		"class":"setup_controll_scroller"
	});
	scroller.slider({min:0, max:255, value:msg_dec["brightness_pos"], 
		slide:function(){
			var msg_int=msg_dec;
			return function(){
				send_color(msg_int["mid"]);
			};
		}(), 
		change:function(){
			var msg_int=msg_dec;
			return function(){
				send_color(msg_int["mid"]);
			};
		}()});
	setupcontrol.append(scroller);
	////////////////// COLOR SLIDER ////////////////////////////

	////////////////// ALARM MANAGER ////////////////////////////
	alarms=$("<div></div>");
	alarms.attr({
		"id" : mid+"_alarms",
	});

	var open=$("<div></div>").attr("id",mid+"_alarms_open");
	open.append($("<div></div>").text("Not-acknowledged").addClass("m2m_text").addClass("inline_block"));
	open.append($("<div></div>").attr("id",mid+"_alarms_open_navigation").text("Navigation").addClass("m2m_text").addClass("alert_navigation"));
	a=$("<div></div>").attr("id",mid+"_alarms_open_display");
	open.append(a);
	a.append($("<div></div>").attr("id",mid+"_alarms_open_stopper"));		
	open.append($("<div></div>").attr("id",mid+"_alarms_open_list").hide());
	open.append($("<div></div>").attr("id",mid+"_alarms_open_start").text("0").hide());
	open.append($("<div></div>").attr("id",mid+"_alarms_open_count").text("10").hide());
	open.append($("<div></div>").attr("id",mid+"_alarms_open_max").hide());
	alarms.append(open);	

	alarms.append($("<hr>"));

	var close=$("<div></div>").attr("id",mid+"_alarms_closed");
	close.append($("<div></div>").text("Acknowledged").addClass("m2m_text").addClass("inline_block"));
	close.append($("<div></div>").attr("id",mid+"_alarms_closed_navigation").text("Navigation").addClass("m2m_text").addClass("alert_navigation"));
	a=$("<div></div>").attr("id",mid+"_alarms_closed_display");
	close.append(a);
	a.append($("<div></div>").attr("id",mid+"_alarms_closed_stopper"));		
	close.append($("<div></div>").attr("id",mid+"_alarms_closed_list").hide());
	close.append($("<div></div>").attr("id",mid+"_alarms_closed_start").text("0").hide());
	close.append($("<div></div>").attr("id",mid+"_alarms_closed_count").text("10").hide());
	close.append($("<div></div>").attr("id",mid+"_alarms_closed_max").hide());
	alarms.append(close);	

	alarms.hide();
	node.append(alarms);
	////////////////// ALARM MANAGER ////////////////////////////
	//<div style="width: 300px;" id="slider1"></div>

	area.append(node);
	//console.log("hb feld in client angebaut");
	/////////////////// CREATE M2M ////////////////////////////(

	show_old_alert_fb(mid,msg_dec["open_alarms"]);
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function set_button_state(b,state){
	if(state==-1 && b.length){
		b.addClass("button_deactivated"); // avoids clickability
	} else if(b.length){
		b.removeClass("button_deactivated");
	};
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function is_button_active(id){
	var button=$(id);
	if(button.length){
		if(button.hasClass("button_deactivated")){
			return true;
		}
	}
	return false;
};

////////////////////////////////////////////// LIVE VIEW /////////////////////////////////////////////
/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function toggle_liveview(mid){
	if(is_button_active("#"+mid+"_toggle_liveview")){
		return;
	};

	if(is_liveview_open(mid)){
		hide_liveview(mid,true);
	} else {
		show_liveview(mid);
	};
};

function is_liveview_open(mid){
	var view = $("#"+mid+"_liveview");
	if(view.is(":visible")){
		return true;
	} else {
		return false;
	}
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function hide_liveview(mid,animation){
	var view = $("#"+mid+"_liveview");
	$("#"+mid+"_toggle_liveview").removeClass("live_sym_active");
	$("#"+mid+"_toggle_liveview_text").removeClass("toggle_liveview_text_active");
	if(view.is(":visible")){
		set_interval(mid,0);
		if(animation){
			view.fadeOut("fast");
		} else {
			view.hide();
		}
	}
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function show_liveview(mid){
	hide_setupcontrol(mid);
	hide_alarms(mid);
	// set button active
	$("#"+mid+"_toggle_liveview").addClass("live_sym_active");
	$("#"+mid+"_toggle_liveview_text").addClass("toggle_liveview_text_active");

	var view = $("#"+mid+"_liveview");

	if(!view.is(":visible")){
		var img=$("#"+mid+"_liveview_pic");		
		img.attr({
			"src":host+"images/support-loading.gif",
			"width":64,
			"height":64
		});
		var txt=$("#"+mid+"_liveview_txt");		
		txt.show();

		// upload speed debug info
		txt=$("#"+mid+"_liveview_up_down_debug");
		txt.hide();

		view.fadeIn("fast");

		// send request
		set_interval(mid,1);
	};
}
///////////////////////// LIVE VIEW //////////////////////////////////

///////////////////////////////////////////// COLOR VIEW /////////////////////////////////////////
/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function toggle_setupcontrol(mid){
	if(is_button_active("#"+mid+"_toggle_setupcontrol")){
		return;
	};

	var view = $("#"+mid+"_setupcontrol");
	if(view.is(":visible")){
		hide_setupcontrol(mid);
	} else {
		show_setupcontrol(mid);
	};
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function hide_setupcontrol(mid){
	var view = $("#"+mid+"_setupcontrol");
	$("#"+mid+"_toggle_setupcontrol").removeClass("color_sym_active");
	$("#"+mid+"_toggle_setupcontrol_text").removeClass("toggle_setupcontrol_text_active");
	if(view.is(":visible")){
		view.fadeOut("fast");
	}
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function show_setupcontrol(mid){
	hide_liveview(mid,true);
	hide_alarms(mid);
	send_color(mid);
	$("#"+mid+"_toggle_setupcontrol").addClass("color_sym_active");
	$("#"+mid+"_toggle_setupcontrol_text").addClass("toggle_setupcontrol_text_active");
	var view = $("#"+mid+"_setupcontrol");
	if(!view.is(":visible")){
		view.fadeIn("fast");
	};
}
///////////////////////// COLOR VIEW //////////////////////////////////

///////////////////////// ALARM VIEW //////////////////////////////////
/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function toggle_alarms(mid){
	if(is_button_active("#"+mid+"_toggle_alarms")){
		return;
	};

	if(is_alarm_open(mid)){
		hide_alarms(mid);
	} else {
		show_alarms(mid);
		get_alarms(mid);
	};
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function is_alarm_open(mid){
	var view = $("#"+mid+"_alarms");
	if(view.is(":visible")){
		return true;
	} else {
		return false;
	};	
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function hide_alarms(mid){
	var view = $("#"+mid+"_alarms");
	$("#"+mid+"_toggle_alarms").removeClass("alarm_sym_active");
	$("#"+mid+"_toggle_alarms_text").removeClass("toggle_alarms_text_active");
	if(view.is(":visible")){
		view.fadeOut("fast");
	}
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function show_alarms(mid){
	hide_setupcontrol(mid);
	hide_liveview(mid,true);
	$("#"+mid+"_toggle_alarms").addClass("alarm_sym_active");
	$("#"+mid+"_toggle_alarms_text").addClass("toggle_alarms_text_active");

	var view = $("#"+mid+"_alarms");
	if(!view.is(":visible")){
		view.fadeIn("fast");
	};

	view = $("#"+mid+"_alarms_open_display");
	view.append(get_loading());
	if(!view.is(":visible")){
		view.fadeIn("fast");
	};

	view = $("#"+mid+"_alarms_closed_display");
	view.append(get_loading());
	if(!view.is(":visible")){
		view.fadeIn("fast");
	};
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function set_alert_button_state(counter,button,txt,open_alarms){
	// the image button
	if(button.length){
		if(open_alarms==0){
			button.text("no alarms");
			button.addClass("alarm_sym");
			button.removeClass("alarm_sym_open_alerts");
		} else if(open_alarms==1) {
			button.text(open_alarms+" alarm");
			button.addClass("alarm_sym_open_alerts");
			button.removeClass("alarm_sym");
		} else {
			button.text(open_alarms+" alarms");
			button.addClass("alarm_sym_open_alerts");
			button.removeClass("alarm_sym");
		}
	};

	// text over the image
	if(counter.length){
		if(open_alarms==0){
			counter.text("");
		} else {
			counter.text(open_alarms);
		};
	};

/*	// Text under the image
	if(open_alarms==0){
		txt.addClass("sym_text_deactivated");
		txt.removeClass("toggle_alarms_text_active");
	} else {
		txt.addClass("toggle_alarms_text_active");
		txt.removeClass("sym_text_deactivated");
	}
*/
}		
///////////////////////// ALARM VIEW //////////////////////////////////

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function state2glow(b,state,det){
	b.removeClass("glow_red");
	b.removeClass("glow_purple");
	b.removeClass("glow_green");
	b.removeClass("glow_yellow");


	if(state==-1){ //disconnected
		b.addClass("glow_purple");
	} else if(state>=1 && det>0){
		b.addClass("glow_red");
	} else if(state>=1 && det==0){
		b.addClass("glow_yellow");
	} else {
		b.addClass("glow_green");
	};
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: mainly by update_state due to incoming state change messages
// arguemnts:	 movement state and detection settings
// what it does: generates a user readable state
// why: 	 to display the cam state
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function state2str(state,det){
	var ret="";
	if(state==0){
		ret = "No motion detected";
	} else if(state==1){
		ret = "movement!";

		if(det==0){
			ret = "Motion, but disarmed";
		} else if(det==1){
			ret = "Alarm!";
		} else if(det==2){
			ret = "Alarm!!";
		} else {
			ret += det.toString();
		}
	} else if(state==-1){
		ret = "disconnected";
	} else if(state==-2){ 
		// just show state
		if(det==0){
			ret="Protection disabled!";
		} else if(det==1){
			ret="Protected";
		} else if(det==2){
			ret="Heavy protected";
		}
	} else {
		ret = state.toString();
	};

	return ret;
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function get_alarms(mid){
	if(con == null){
		return;
	}
	var cmd_data = { 
		"cmd":"get_alert_ids",
		"mid":mid, 
		"open_start": parseInt($("#"+mid+"_alarms_open_start").text()),
		"open_end": parseInt($("#"+mid+"_alarms_open_count").text()),
		"closed_start": parseInt($("#"+mid+"_alarms_closed_start").text()),
		"closed_end": parseInt($("#"+mid+"_alarms_closed_count").text())
	};
	//console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
};	

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function set_interval(mid,on_off){
	if(con == null){
		return;
	}
	var cmd_data = { "cmd":"set_interval", "mid":mid, "interval":on_off};
	con.send(JSON.stringify(cmd_data));

	// active / deactivate fast HB, updates once per second, shows server debug
	/*if(interval==0){
		cmd_data = { "cmd":"hb_fast", "active":0};
	} else {
		cmd_data = { "cmd":"hb_fast", "active":1};
	}
	con.send(JSON.stringify(cmd_data));*/

	//console.log(JSON.stringify(cmd_data));
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: user click on button 'on/off'
// arguemnts:	 user to track who deactivated the detection, area and '*' for on, '/' for off
// what it does: send a message
// why: 	 e.g. activate the alert even if someone forget his phone at home
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function set_override(user,area,on_off){
	if(con == null) {
		return;
	}
	var cmd_data = { "cmd":"set_override", "rule":on_off, "area":area, "duration":"0"};
	//console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function createRainbowDiv(s){
	var gradient = $("<div>").css({display:"flex", height:"100%"});
	if(s>0){
		for (var i = 0; i<255; i++){
			gradient.append($("<div>").css({"background-color":'hsl('+i+','+s+'%,50%)',flex:1}));
		}
		gradient.append($("<div>").css({"background-color":'hsl(300,100%,94%)',flex:1}));

	} else {
		for (var i = 0; i<=255; i++){
			gradient.append($("<div>").css({"background-color":'rgb('+i+','+i+','+i+')',flex:1}));
		}
	}
	return gradient;
}

/////////////////////////////////////////// SEND COLOR //////////////////////////////////////////
// triggered by: movement of the color/brightness slider
// arguemnts:	 MID
// what it does: grabs to pos of the slider and sends it to the server
// why: 	 to change the color of the m2m
/////////////////////////////////////////// SEND COLOR //////////////////////////////////////////

function send_color(mid) {
	var c=($("<a>").css({"background-color":'hsl('+$( "#colorslider_"+mid ).slider( "value" )+',100%,50%)'})).css("background-color");
	var rgb = c.replace(/^(rgb|rgba)\(/,'').replace(/\)$/,'').replace(/\s/g,'').split(',');
	if($.isNumeric(rgb[0])){
		var color=$("#colorslider_"+mid).slider( "value" );
		var brightness=$("#brightnessslider_"+mid).slider( "value" );
		var mul=brightness/255;
		if(color==255){
			rgb[0]=255;
			rgb[1]=255;
			rgb[2]=255;
		};

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

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function update_hb(mid,ts){
	if($("#"+mid+"_lastseen").length){
		var a = new Date(parseFloat(ts)*1000);
		var min = a.getMinutes() < 10 ? '0' + a.getMinutes() : a.getMinutes(); 
		var hour = a.getHours();
		var text = "Ping "+hour+":"+min;

		var delay=parseInt((Date.now()-(1000*parseFloat(ts)))/1000);
		if(delay>86400){		
			text="Last online "+a.getFullYear()+"/"+(a.getMonth()+1)+"/"+a.getDate();
		} else if(delay<999) {
			text += " - delay "+delay+" sec";
		};

		$("#"+mid+"_lastseen").text(text);
		//console.log("hb ts updated");
	}
}
/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function update_state(account,area,mid,state,detection,rm,alarm_ws){
	//console.log("running update state on "+mid+"/"+state+"/"+rm);

	// set the rulemanager text explainaition for the complete area
	if(state>=0){
		$("#"+account+"_"+area+"_status").click(function(){
			var rm_int=rm;
			return function(){
				txt2fb(format_rm_status(rm_int));
			};
		}());
	};
	// set the rulemanager text explainaition

	// text state of the m2m
	var e=$("#"+mid+"_state");
	if(e.length){
		e.text(state2str(state,detection));
		if(alarm_ws==0){ // if alarm_ws is == 1, we'll send images to the WS on an alert and the site show show an popup (created below)
			e.text(e.text()+", silent mode");
		};
	}
	// text state of the m2m

	// icons of the area
	e=$("#"+account+"_"+area+"_icon");
	if(e.length){
		if(detection>0){
			e.removeClass("area_sym_not_protected");
			e.addClass("area_sym_protected");
		} else {
			e.addClass("area_sym_not_protected");
			e.removeClass("area_sym_protected");
		}
	}
	// icons of the area
	// text state of the area
	e=$("#"+account+"_"+area+"_status");
	if(e.length){
		e.text(state2str(-2,detection));
		if(detection>0){
			e.removeClass("area_sym_not_protected");
			e.addClass("area_sym_protected");
		} else {
			e.addClass("area_sym_not_protected");
			e.removeClass("area_sym_protected");
		}
	}
	// text state of the area

	// activate/deactivate buttons of the area
/*	if(detection>0){
		$("#"+account+"_"+area+"_on").hide();
		$("#"+account+"_"+area+"_off").show();
	} else {
		$("#"+account+"_"+area+"_on").show();
		$("#"+account+"_"+area+"_off").hide();
	};*/
	// activate/deactivate buttons of the area

	// glow icon state of the m2m
	if($("#"+mid+"_glow").length){
		state2glow($("#"+mid+"_glow"),state,detection);
	}
	// glow icon state of the m2m
	
	// POP UP
	if(detection>0 && state>0 && alarm_ws>0){
	 	// if we change to alert-state, show popup with shortcut to the liveview
		show_alert_fb(mid);
	} else {
		// if we change to non-alert-state and there is still the alert popup, show the old_alert popup
		if($("#"+mid+"_liveview_alert_fb").length && alarm_ws>0){
			var open_alarms=$("#"+mid+"_alarm_counter");
			if(open_alarms.length){
				show_old_alert_fb(mid,open_alarms.text());
			}
		};
	}
	// POP UP
	
	// make buttons available/unavailable
	var lv=$("#"+mid+"_toggle_liveview");
	var cv=$("#"+mid+"_toggle_setupcontrol");
	var av=$("#"+mid+"_toggle_alarms");
	var lt=$("#"+mid+"_toggle_liveview_text");
	var ct=$("#"+mid+"_toggle_setupcontrol_text");
	var at=$("#"+mid+"_toggle_alarms_text");
	if(state<0){
		lv.addClass("button_deactivated"); // avoids clickability
		lv.addClass("live_sym_not_available");
		lv.removeClass("live_sym");

		lt.addClass("sym_text_not_available");
		lt.removeClass("toggle_liveview_text_active");
	
		cv.addClass("button_deactivated"); // avoids clickability
		cv.addClass("color_sym_not_available");
		cv.removeClass("color_sym");

		ct.addClass("sym_text_not_available");
		ct.removeClass("toggle_setupcontrol_text_active");

		hide_liveview(mid,true);
		hide_setupcontrol(mid);
	} else {
		lv.removeClass("button_deactivated");
		lv.removeClass("live_sym_not_available");
		lv.addClass("live_sym");		
		lt.removeClass("sym_text_not_available");

		cv.removeClass("button_deactivated");
		cv.removeClass("color_sym_not_available");
		cv.addClass("color_sym");
		ct.removeClass("sym_text_not_available");
	}
	// make buttons available/unavailable

}


/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function rem_menu(){
	var menu=$("#menu");
	if(menu.length){
		menu.remove();
	};

	var hamb=$("#hamb");
	if(hamb.length){
		hamb.remove();
	};
};


/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function add_menu(){
	/******* add menu ******/
	// menu itsself
	var menu=$("#menu");
	if(menu.length){
		rem_menu();
	};

	menu=$("<div></div>");
	menu.attr("id","menu");
	menu.addClass("menu");
	
	//////////////// rm setup //////////////////
	var f=function(){
		var box=$("#rm_box");
		if(box.length){
			box.toggle();	
		}
	};
	add_sidebar_entry(menu,f,"rules","style");
	var box=$("<div></div>");
	box.attr("id","rm_box");
	box.text("here is a lot of content needed, like a the current rm stuff per area and an area where we can add new rules");
	box.hide();
	menu.append(box);	
	//////////////// rm setup //////////////////

	//////////////// area setup //////////////////
	var f=function(){
		var box=$("#areas_box");
		if(box.length){
			box.toggle();	
		}
	};
	add_sidebar_entry(menu,f,"areas","home");
	var box=$("<div></div>");
	box.attr("id","areas_box");
	box.text("here is a lot of content needed, like a list of all aereas, how to set the coordiantes per cam and how to create and delete them");
	box.hide();
	menu.append(box);	
	//////////////// area setup //////////////////

	//////////////// camera setup //////////////////
	var f=function(){
		var box=$("#cameras_box");
		if(box.length){
			box.toggle();	
		}
	};
	add_sidebar_entry(menu,f,"cameras","camera_enhance");
	var box=$("<div></div>");
	box.attr("id","cameras_box");
	box.text("here is a lot of content needed, like a list of all cameras, if they stream in HD or vga, if there should be alerts during stream, what area thez belog to");
	box.hide();
	menu.append(box);	
	//////////////// camera setup //////////////////

	//////////////// user setup //////////////////
	var f=function(){
		var box=$("#users_box");
		if(box.length){
			box.toggle();	
			login_entry_button_state("-1","show");	// scale the text fields for the "new" entry = -1
		}
	};
	add_sidebar_entry(menu,f,"users","group");
	var box=$("<div></div>");
	box.attr("id","users_box");
	box.text("here is a lot of content needed, like a list of all users, if they stream in HD or vga, if there should be alerts during stream, what area thez belog to");
	box.hide();
	menu.append(box);	
	//////////////// user setup //////////////////


	//////////////// logout //////////////////
	var f=function(){
			g_user="nongoodlogin";
			g_pw="nongoodlogin";
			c_set_login(g_user,g_pw);
			txt2fb(get_loading("","Signing you out..."));
			fast_reconnect=1;
			con.close();

			// hide menu
			rem_menu();
	};
	add_sidebar_entry(menu,f,"log-out","vpn_key");
	//////////////// logout //////////////////

	////////////// hidden data_fields /////////////
	var h=$("<div></div>");
	h.attr("id","list_cameras");
	h.hide();
	menu.append(h);

	h=$("<div></div>");
	h.attr("id","list_area");
	h.hide();
	menu.append(h);
	////////////// hidden data_fields /////////////


	menu.insertAfter("#clients");
	

	var hamb=$("<div></div>");
	hamb.click(function(){
		return function(){
			toggle_menu();
		}
	}());
	hamb.attr("id","hamb");
	hamb.addClass("hamb");
	var a=$("<div></div>");
	var b=$("<div></div>");
	var c=$("<div></div>");
	a.addClass("hamb_l");
	b.addClass("hamb_l");
	c.addClass("hamb_l");
	hamb.append(a);
	hamb.append(b);
	hamb.append(c);
	hamb.insertAfter("#clients");
	/******* add menu ******/
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function add_camera_entry(m_m2m,field){
	// create header
	var cam_header=$("<div></div>");
	cam_header.addClass("sidebar_area_entry");
	cam_header.addClass("inline_block");
	field.append(cam_header);

	// create cam div
	var cam_icon_name=$("<div></div>");
	cam_icon_name.addClass("float_left");
	cam_icon_name.addClass("inline_block");
	cam_header.append(cam_icon_name);				

	// add icon
	var cam_icon=$("<i></i>");
	cam_icon.addClass("material-icons");
	cam_icon.addClass("float_left");
	cam_icon.text("camera_enhance");
	cam_icon_name.append(cam_icon);
			
	// first the name
	var cam_name=$("<div></div>");
	cam_name.text(m_m2m["alias"]+" v."+m_m2m["v_short"]+"/"+g_version["v_short"]);
	cam_name.addClass("float_right");
	cam_name.addClass("sidebar_area_name");
	cam_icon_name.append(cam_name);

	var cam_update_button=$("<div></div>");
	cam_update_button.addClass("float_right");
	cam_update_button.click(function(){
		var int_mid=m_m2m["mid"];
		return function(){
			git_update(int_mid);
		};
	}());
//	if(parseInt(m_m2m["v_short"])<parseInt(g_version["v_short"])){
		cam_update_button.text("UPDATE ");
//	} else {
//		cam_update_button.hide(); 2do
//	}
	cam_icon_name.append(cam_update_button);

	//////////////// add fps dropdown ////////////////////
	var fps_select=$("<select></select>");
	fps_select.attr({
		"id": m_m2m["mid"]+"_fps_select",
		"class":"sidebar_select"
	});
	// load from message
	var default_t=parseFloat(m_m2m["frame_dist"]);
	if(!$.isNumeric(default_t)){
		default_t=1/2;
	};
	// create field
	var t=1/16;
	var fps_text;
	for(var i=0; i<12; i++) {
		if(1/t >= 1){
			fps_text = 1/t+" fps (a frame every "+Math.round(t*100)/100+" sec)";
		} else {
			fps_text = "1/"+t+" fps (a frame every "+t+" sec)";
		};
		// set selected option for the 2fps option
		if(t==default_t){
			fps_select.append($('<option></option>').val(t).html(fps_text).prop('selected', true));
		} else {
			fps_select.append($('<option></option>').val(t).html(fps_text));
		};
		// calc the next framerate
		if(t<1){
			t*=2;
		} else {
			t+=1;
		}
	};
	fps_select.change(function(){
		var mid_int=m_m2m["mid"];
		return function(){
			update_cam_parameter(mid_int);
		}
	}());

	field.append(fps_select);
	//////////////// add fps dropdown ////////////////////

	///////////////// quality selector //////////////////////
	var qual_select=$("<select></select>");
	qual_select.attr({
		"id": m_m2m["mid"]+"_qual_select",
		"class":"sidebar_select"
	});
	var hd_sel=true;
	var vga_sel=false;
	if(m_m2m["resolution"]!="HD"){
		hd_sel=false;
		vga_sel=true;
	}
	qual_select.append($('<option></option>').val("HD").html("HD resolution, slow").prop('selected', hd_sel));
	qual_select.append($('<option></option>').val("VGA").html("VGA resolution, fast").prop('selected', vga_sel));
	qual_select.change(function(){
		var mid_int=m_m2m["mid"];
		return function(){
			update_cam_parameter(mid_int);
		}
	}());
	field.append(qual_select);
	///////////////// quality selector //////////////////////

	/////////// alarm while streaming selector //////////////////
	var alarm_while_stream_select=$("<select></select>");
	alarm_while_stream_select.attr({
		"id": m_m2m["mid"]+"_alarm_while_stream_select",
		"class":"sidebar_select"
	});

	var no_alarm_sel=true;
	var alarm_sel=false;
	if(m_m2m["alarm_while_streaming"]==1 || m_m2m["alarm_while_streaming"]=="alarm"){
		no_alarm_sel=false;
		alarm_sel=true;
	}
	alarm_while_stream_select.append($('<option></option>').val("no_alarm").html("No alarm while streaming (Bad power supply)").prop('selected', no_alarm_sel));
	alarm_while_stream_select.append($('<option></option>').val("alarm").html("Still watch for movement (good power supply)").prop('selected',alarm_sel));
	alarm_while_stream_select.change(function(){
		var mid_int=m_m2m["mid"];
		return function(){
			update_cam_parameter(mid_int);
		}
	}());
	field.append(alarm_while_stream_select);
	/////////// alarm while streaming selector //////////////////

	/////////// areas switch //////////////////
	var area_select=$("<select></select>");
	area_select.attr({
		"id": m_m2m["mid"]+"_area_select",
		"class":"sidebar_select"
	});
				
	for(var i=0; i<g_areas.length; i++){
		sel=false;
		if(m_m2m["area"]==g_areas[i]["area"]){
			sel=true;
		}
		area_select.append($('<option></option>').val(g_areas[i]["id"]).html(g_areas[i]["area"]).prop('selected', sel));
	}
	area_select.change(function(){
		var mid_int=m_m2m["mid"];
		return function(){
			update_cam_parameter(mid_int);
		}
	}());
	field.append(area_select);
	/////////// areas switch //////////////////
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function add_rm_entry(field,m_rm_area){

	///// create header /////
	var area_header=$("<div></div>");
	area_header.addClass("sidebar_area_entry");
	area_header.addClass("inline_block");
	field.append(area_header);

	// create area div
	var area_icon_name=$("<div></div>");
	area_icon_name.addClass("float_left");
	area_icon_name.addClass("inline_block");
	area_header.append(area_icon_name);				

	// add icon
	var area_icon=$("<i></i>");
	area_icon.addClass("material-icons");
	area_icon.addClass("float_left");
	area_icon.text("home");
	area_icon_name.append(area_icon);
			
	// first the name
	var area_name=$("<div></div>");
	area_name.text(m_rm_area["area"]);
	area_name.addClass("float_right");
	area_name.addClass("sidebar_area_name");
	area_icon_name.append(area_name);
	///// create header /////

	///// now the ruels /////
	var nobody_at_my_geo_area_active=false;
	for(var b=0;b<m_rm_area["rules"].length;b++){
		var rm_rule=$("<div></div>");
		if(m_rm_area["rules"][b][1]=="nobody_at_my_geo_area"){
			nobody_at_my_geo_area_active=true;
		} else {
			rm_rule.text(m_rm_area["rules"][b][1]+","+m_rm_area["rules"][b][2]+","+m_rm_area["rules"][b][3]);
		};
		//rm_header.append(rm_rule);
	};

	///////// GPS /////////
	var geo_select=$("<select></select>");
	geo_select.attr({
		"id": m_rm_area["area"]+"_geo_area",
		"class":"sidebar_select"
	});
	geo_select.append($('<option></option>').val("1").html("geofencing active").prop('selected', nobody_at_my_geo_area_active));
	geo_select.append($('<option></option>').val("0").html("no geofencing").prop('selected', !nobody_at_my_geo_area_active));
	geo_select.change(function(){
		var int_id=m_rm_area["area"];
		return function(){
			var geo_fencing=$("#"+int_id+"_geo_area");
			if(geo_fencing.length){
				update_rule_geo(int_id,geo_fencing.val());
			};
		}
	}());
	field.append(geo_select);
	///////// GPS /////////
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function add_area_entry(field,m_area){
	// create header entry
	var area_entry=$("<div></div>");
	area_entry.addClass("sidebar_area_entry");
	area_entry.addClass("inline_block");
	field.append(area_entry);

	// create home div
	var area_icon_name=$("<div></div>");
	area_icon_name.addClass("float_left");
	area_icon_name.addClass("inline_block");
	area_entry.append(area_icon_name);				

	// add icon
	var area_icon=$("<i></i>");
	area_icon.addClass("material-icons");
	area_icon.addClass("float_left");
	area_icon.text("home");
	if(m_area["id"]==-1){
		area_icon.text("add");
	};
	area_icon_name.append(area_icon);

	// first the name
	var area_name=$("<div></div>");
	area_name.attr("id","m_"+m_area["id"]+"_name");
	area_name.text(m_area["area"]);
	area_name.addClass("float_right");
	area_name.addClass("sidebar_area_name");
	if(m_area["id"]==-1){
		area_name.hide();
	}
	area_icon_name.append(area_name);


	var area_num_m2m=$("<div></div>");
	area_num_m2m.attr("id","m_"+m_area["id"]+"_num_m2m");
	area_num_m2m.text(m_area["m2m_count"]);
	area_num_m2m.hide();
	area_entry.append(area_num_m2m);

	var area_name_edit=$("<input></input>");
	area_name_edit.attr("id","m_"+m_area["id"]+"_name_edit");
	area_name_edit.val(m_area["area"]);
	area_name_edit.addClass("sidebar_area_name");
	if(m_area["id"]!=-1){
		area_name_edit.hide();
	} else {
		area_name_edit.val("Enter area name");
		area_name_edit.focus(function(){
			if($(this).val()=="Enter area name"){
				$(this).val("");
			}
		});
	};

	area_entry.append(area_name_edit);

	var area_lat=$("<input></input>");
	area_lat.attr("id","m_"+m_area["id"]+"_map_lat");
	area_lat.attr("type","text");
	area_lat.val(m_area["latitude"]); 
	area_lat.hide();
	area_entry.append(area_lat);

	var area_lng=$("<input></input>");
	area_lng.attr("id","m_"+m_area["id"]+"_map_lng");
	area_lng.val(m_area["longitude"]);
	area_lng.attr("type","text");
	area_lng.hide();
	area_entry.append(area_lng);


	var area_buttons=$("<div></div>");
	area_buttons.addClass("float_right");
	area_buttons.addClass("inline_block");
	area_entry.append(area_buttons);


	// the save button
	var area_save=$("<i></i>");
	area_save.attr("id","m_"+m_area["id"]+"_map_save");
	area_save.attr("type","submit");
	area_save.addClass("material-icons");
	area_save.addClass("sidebar_icons");
	area_save.text("save");
	area_save.click(function(){
		var int_area_save=m_area["id"]; // reminder, do not save arrays here, i think that is due to the nature or pointer vs value
		return function(){
			var map=$("#m_"+int_area_save+"_map");
			var discard=$("#m_"+int_area_save+"_map_disc");
			var lng=$("#m_"+int_area_save+"_map_lng");
			var lat=$("#m_"+int_area_save+"_map_lat");
			var save=$("#m_"+int_area_save+"_map_save");
			var edit=$("#m_"+int_area_save+"_map_edit");
			var remove = $("#m_"+int_area_save+"_map_rem");
			var name=$("#m_"+int_area_save+"_name");
			var name_edit=$("#m_"+int_area_save+"_name_edit");
			if(map.length && lng.length && lat.length && save.length && edit.length && name.length && name_edit.length){
				map.hide();
				lng.hide();
				discard.hide();
				lat.hide();
				save.hide();
				name_edit.hide();
				name.text(name_edit.val());
				name.show();
				edit.show();
				remove.show();
				update_area(int_area_save, name_edit.val(), lat.val(), lng.val());
				request_all_rules();
			};
			if(int_area_save==-1){
				request_all_areas();
			}; 
		};
	}());
	area_save.hide();
	area_buttons.append(area_save);

	// the edit area button
	var area_map_edit=$("<i></i>");
	area_map_edit.attr("id","m_"+m_area["id"]+"_map_edit");
	area_map_edit.addClass("material-icons");
	area_map_edit.addClass("sidebar_icons");
	if(m_area["id"]!=-1){
		area_map_edit.text("mode_edit");
	} else {
		area_map_edit.text("location_searching");
	}
	area_map_edit.addClass("button");
	area_map_edit.click(function(){
		var int_area_edit=m_area["id"];
		return function(){
			var map = $("#m_"+int_area_edit+"_map");
			var lng = $("#m_"+int_area_edit+"_map_lng");
			var lat = $("#m_"+int_area_edit+"_map_lat");
			var save = $("#m_"+int_area_edit+"_map_save");
			var edit = $("#m_"+int_area_edit+"_map_edit");
			var name = $("#m_"+int_area_edit+"_name");
			var discard=$("#m_"+int_area_edit+"_map_disc");
			var remove = $("#m_"+int_area_edit+"_map_rem");
			var name_edit = $("#m_"+int_area_edit+"_name_edit");
			if(map.length && lng.length && lat.length && save.length && edit.length && name.length && name_edit.length){
				map.show();
				//lng.show();
				//lat.show();
				discard.show();
				save.show();
				name_edit.show();
				name.hide();
				edit.hide();
				remove.hide();
				show_map(parseFloat(lat.val()),parseFloat(lng.val()),map,lat,lng);
				$("#menu").animate({
					scrollTop: name_edit.offset().top-($(window).height()/20)
				},1000);

			} else {
				alert("ele not found "+int_area_edit+":"+map.length +","+ lng.length +","+ lat.length +","+ save.length +","+ edit.length);
			}
		};
	}());
	area_buttons.append(area_map_edit);

	// the remove button
	var area_remove=$("<i></i>");
	area_remove.attr("id","m_"+m_area["id"]+"_map_rem");
	area_remove.text("delete");
	area_remove.addClass("material-icons");
	area_remove.addClass("sidebar_icons");
	if(m_area["m2m_count"]>0){
		area_remove.addClass("md-dark");
		area_remove.addClass("md-inactive");
	};
	if(m_area["id"]==-1){
		area_remove.hide();
	};
	area_remove.click(function(){
		var int_area_remove=m_area["id"]; // reminder, do not save arrays here, i think that is due to the nature or pointer vs value
		var int_area_m2m_count=m_area["m2m_count"]; // reminder, do not save arrays here, i think that is due to the nature or pointer vs value
		return function(){
			if(int_area_m2m_count==0){
				if( confirm('Are you sure to delete this area?')){
					remove_area(int_area_remove);
					request_all_areas();
				};
			} else {
				alert("You can not delete this area, it has still "+int_area_m2m_count+" cams in it");
			};
		};
	}());
	area_buttons.append(area_remove);

	// the discard button
	var area_discard=$("<i></i>");
	area_discard.attr("id","m_"+m_area["id"]+"_map_disc");
	area_discard.text("clear");
	area_discard.addClass("sidebar_icons");
	area_discard.addClass("material-icons");
	area_discard.hide();
	area_discard.click(function(){
		var int_area_discard=m_area["id"]; // reminder, do not save arrays here, i think that is due to the nature or pointer vs value
		return function(){
			var map=$("#m_"+int_area_discard+"_map");
			var lng=$("#m_"+int_area_discard+"_map_lng");
			var lat=$("#m_"+int_area_discard+"_map_lat");
			var save=$("#m_"+int_area_discard+"_map_save");
			var edit=$("#m_"+int_area_discard+"_map_edit");
			var remove = $("#m_"+int_area_discard+"_map_rem");
			var name=$("#m_"+int_area_discard+"_name");
			var name_edit=$("#m_"+int_area_discard+"_name_edit");
			var discard=$("#m_"+int_area_discard+"_map_disc");
			if(map.length && lng.length && lat.length && save.length && edit.length && name.length && name_edit.length){
				map.hide();
				lng.hide();
				lat.hide();
				save.hide();
				if(int_area_discard!=-1){	
					name_edit.hide();
					name.show();
				} else {
					name_edit.val("Enter area name");
				};
				edit.show();
				discard.hide();
				if(int_area_discard!=-1){
					remove.show();
				};
			};
			
		};
	}());
	area_buttons.append(area_discard);

	// the map itsself
	var area_map=$("<div></div>");
	area_map.attr("id","m_"+m_area["id"]+"_map");
	area_map.addClass("sidebar_area_map");
	area_map.css("height",350);
	area_map.hide();
	field.append(area_map);

	var spacer=$("<hr>");
	field.append(spacer);
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function add_login_entry(field,m_login){
	// create header entry
	var login_entry=$("<div></div>");
	login_entry.addClass("sidebar_area_entry");
	login_entry.addClass("inline_block");
	login_entry.attr("id","u_"+m_login["id"]+"_outer");
	field.append(login_entry);

	// create user div
	var login_info=$("<div></div>");
	login_info.addClass("float_left");
	login_info.addClass("inline_block");
	login_info.attr("id","u_"+m_login["id"]+"_info");
	//login_entry.append(login_info);				

	// add icon
	var login_icon=$("<i></i>");
	login_icon.addClass("material-icons");
	login_icon.addClass("float_left");
	login_icon.addClass("inline_block");
	login_icon.css("vertical-align","top");
	login_icon.text("person");
	if(m_login["id"]==-1){
		login_icon.text("add");
	};
	//login_info.append(login_icon);
	login_entry.append(login_icon);

	// keep everything right - multi rows
	var login_field_wrapper=$("<div></div>");
	login_field_wrapper.attr("id","u_"+m_login["id"]+"_field_wrapper");
	login_field_wrapper.addClass("inline_block");
	login_field_wrapper.css("margin-top", "3px");
	login_field_wrapper.css("width", "50%");
	
	login_entry.append(login_field_wrapper);

	// first the name
	var login_name=$("<div></div>");
	login_name.attr("id","u_"+m_login["id"]+"_name_display");
	login_name.css("margin-left", "5px");
	login_name.text(m_login["login"]);
	if(m_login["id"]==-1){
		login_name.hide();
	}
	login_field_wrapper.append(login_name);

	// the name changing field 
	var login_name_edit=$("<input></input>");
	login_name_edit.addClass("inline_block");
	login_name_edit.css("width", "100%");
	login_name_edit.css("margin-left", "5px");
	login_name_edit.attr("id","u_"+m_login["id"]+"_name_edit");
	login_name_edit.val(m_login["login"]);
	login_name_edit.keyup(function(e){
		var m_id=m_login["id"];
		if(e.keyCode == 13){
			if(!$("#u_"+m_id+"_pw1").is(":visible")){
				$("#u_"+m_id+"_edit").click();
			}
			$("#u_"+m_id+"_pw1").focus();
		};
	});
	if(m_login["id"]!=-1){	// hide it as long as we ar not the "new"
		login_name_edit.hide();
	} else {
		login_name_edit.val("Enter login name");
		login_name_edit.focus(function(){
			if($(this).val()=="Enter login name"){
				$(this).val("");
			}
		});
	};
	login_field_wrapper.append(login_name_edit);

	// first password field
	var login_pw1=$("<input></input>");
	login_pw1.attr("id","u_"+m_login["id"]+"_pw1");
	login_pw1.css("width", "100%");
	login_pw1.css("margin-left", "5px");
	login_pw1.attr("type","text");
	login_pw1.keyup(function(e){
		var m_id=m_login["id"];
		if(e.keyCode == 13){
			$("#u_"+m_id+"_pw2").focus();
		};
	});
	login_pw1.focus(function(){
		if($(this).val()=="Modify password" || $(this).val()=="Create password"){
			$(this).attr("type","password");
			$(this).val("");
		}
	});
	login_pw1.hide();
	login_field_wrapper.append(login_pw1);

	// second password field
	var login_pw2=$("<input></input>");
	login_pw2.attr("id","u_"+m_login["id"]+"_pw2");
	login_pw2.css("margin-left", "5px");
	login_pw2.css("width", "100%");
	login_pw2.attr("type","text");
	login_pw2.keyup(function(e){
		var m_id=m_login["id"];
		if(e.keyCode == 13){
			$("#u_"+m_id+"_save").click();
		};
	});
	login_pw2.focus(function(){
		if($(this).val()=="Confirm password" || $(this).val()=="Confirm new password"){
			$(this).attr("type","password");
			$(this).val("");
		}
	});
	login_pw2.hide();
	login_field_wrapper.append(login_pw2);

	// the aggregator for all the buttons
	var login_buttons=$("<div></div>");
	login_buttons.attr("id","u_"+m_login["id"]+"_buttons");
	login_buttons.addClass("float_right");
	login_buttons.addClass("inline_block");
	login_entry.append(login_buttons);

	// the save button
	var login_save=$("<i></i>");
	login_save.attr("id","u_"+m_login["id"]+"_save");
	login_save.attr("type","submit");
	login_save.addClass("material-icons");
	login_save.addClass("sidebar_icons");
	login_save.text("save");
	login_save.click(function(){
		var int_login_id=m_login["id"]; // reminder, do not save arrays here, i think that is due to the nature or pointer vs value
		return function(){
			var name = $("#u_"+int_login_id+"_name_edit");
			var pw1 = $("#u_"+int_login_id+"_pw1");
			var pw2 = $("#u_"+int_login_id+"_pw2");
			if(pw1.val()==""){
				alert("you have to enter a non-empty password");
			} else if(pw1.val()==pw2.val()){
				update_login(int_login_id,name.val(),pw1.val());
			} else {
				alert("The password do not match!");
			};
		};
	}());
	login_save.hide();
	login_buttons.append(login_save);

	// the edit login button
	var login_edit=$("<i></i>");
	login_edit.attr("id","u_"+m_login["id"]+"_edit");
	login_edit.addClass("material-icons");
	login_edit.addClass("sidebar_icons");
	if(m_login["id"]==-1){
		login_edit.text("vpn_key");
	} else {
		login_edit.text("mode_edit");
	}
	login_edit.addClass("button");
	login_edit.click(function(){
		var int_login_id=m_login["id"];
		return function(){
			login_entry_button_state(int_login_id,"edit");
		};
	}());
	login_buttons.append(login_edit);

	// the remove button
	var login_remove=$("<i></i>");
	login_remove.attr("id","u_"+m_login["id"]+"_rem");
	login_remove.text("delete");
	login_remove.addClass("material-icons");
	login_remove.addClass("sidebar_icons");
	if(g_logins.length<=1){
		login_remove.addClass("md-dark");
		login_remove.addClass("md-inactive");
	};
	if(m_login["id"]==-1){
		login_remove.hide();
	};
	login_remove.click(function(){
		var int_login_id=m_login["id"]; // reminder, do not save arrays here, i think that is due to the nature or pointer vs value
		return function(){
			if(g_logins.length>1){
				if( confirm('Are you sure to delete this login?')){
					//remove_login(int_login_id);
					//request_all_logins();
					login_entry_button_state(int_login_id,"show");			
					remove_logins(int_login_id);
					request_all_logins();
				};
			} else {
				alert("You can not delete the last user");
			};
		};
	}());
	login_buttons.append(login_remove);

	// the discard button
	var login_discard=$("<i></i>");
	login_discard.attr("id","u_"+m_login["id"]+"_disc");
	login_discard.text("clear");
	login_discard.addClass("sidebar_icons");
	login_discard.addClass("material-icons");
	login_discard.hide();
	login_discard.click(function(){
		var int_login_id=m_login["id"]; // reminder, do not save arrays here, i think that is due to the nature or pointer vs value
		return function(){
			login_entry_button_state(int_login_id,"show");			
		};
	}());
	login_buttons.append(login_discard);

	var spacer=$("<hr>");
	field.append(spacer);
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function login_entry_button_state(m_login_id,state){
	var save = $("#u_"+m_login_id+"_save");
	var discard = $("#u_"+m_login_id+"_disc");
	var pw = $("#u_"+m_login_id+"_pw");
	var pw1 = $("#u_"+m_login_id+"_pw1");
	var pw2 = $("#u_"+m_login_id+"_pw2");
	var edit = $("#u_"+m_login_id+"_edit");
	var name_display = $("#u_"+m_login_id+"_name_display");
	var name_edit = $("#u_"+m_login_id+"_name_edit");
	var remove = $("#u_"+m_login_id+"_rem");
	var admin = $("#u_"+m_login_id+"_admin");

	save.hide();
	discard.hide();
	edit.hide();
	name_display.hide();
	name_edit.hide();
	remove.hide();
	admin.hide();
	pw.hide();
	pw1.hide();
	pw2.hide();

	if(state=="show"){
		if(m_login_id!=-1){
			edit.show();
			name_display.show();
			name_edit.val(name_display.text());
			remove.show();
		} else {
			edit.show();
			name_edit.val("Enter login name");
			name_edit.show();
		}
	} else if(state=="edit"){
		pw1.attr("type","text");
		pw2.attr("type","text");
		if(m_login_id!=-1){
			pw1.val("Modify password");
			pw2.val("Confirm password");
		} else {
			pw1.val("Create password");
			pw2.val("Confirm password");
		}
		save.show();
		discard.show();
		name_edit.show();
		admin.show();
		pw.show();
		pw1.show();
		pw2.show();
	}
	// scale text field to 92% of available width
	var left=$("#u_"+m_login_id+"_field_wrapper").position().left;
	var right=$("#u_"+m_login_id+"_buttons").position().left;
	$("#u_"+m_login_id+"_field_wrapper").outerWidth((right-left)*0.92);

};
/////////////////////////////////////////// ADD MENU ENTRY //////////////////////////////////////////
// triggered by:	add_menu()
// arguemnts:	 	
// what it does: 	shows an entry
// why: 	 	GUI
/////////////////////////////////////////// ADD MENU ENTRY //////////////////////////////////////////
function add_sidebar_entry(menu,f,text,icon){
	//////////////// add title //////////////////
	var title=$("<div></div>");
	title.addClass("menu_spacer");
	title.addClass("inline_block");
	title.click(f);
	menu.append(title);	

	// insert name + icon block
	var title_name_icon=$("<div></div>");
	title_name_icon.addClass("float_left");
	title_name_icon.addClass("menu_spacer_name");
	title_name_icon.addClass("inline_block");
	title.append(title_name_icon);

	// insert name into title
	var title_name=$("<div></div>");
	title_name.text(text);
	title_name.addClass("menu_spacer_name");
	title_name.addClass("float_right");
	title_name.attr("id","users_title");
	title_name_icon.append(title_name);

	// insert sym into title
	var title_sym=$("<i></i>");
	title_sym.text(icon);
	title_sym.addClass("material-icons");
	title_sym.addClass("float_left");
	title_name_icon.append(title_sym);
}

/////////////////////////////////////////// TOGGLE_MENU //////////////////////////////////////////
// triggered by:	user click
// arguemnts:	 	none
// what it does: 	shows the menu and requests info
// why: 	 	GUI
/////////////////////////////////////////// TOGGLE_MENU //////////////////////////////////////////

function toggle_menu(){
	var m=$("#menu");
	if(m.length){
		if(m.hasClass("menu_active")){
			/// HIDE THE MENU ///
			m.removeClass("menu_active");
			// super messy hamb handling
			// datach it from the MENU and make it standalone
			var hamb=$("#hamb");
			hamb.detach();
			hamb.insertAfter("#clients");
			// remove and reattache on click handle, sometimes not working without this
			hamb.off();
			hamb.click(function(){ toggle_menu(); });
			// set the position do be absolute floating on the upper left corner
			hamb.css("position", "absolute");
			// since the hamb moved in the DOM, we have to move it out fast, without animation  and then perform another transform with animation
			hamb.css("transition","all 0.0s ease-in-out").css("transform", "translate("+(m.outerWidth(true)-$("#hamb").outerWidth()-30)+"px, 0px)").css("transition","all 0.75s ease-in-out").css("transform", "translate(0px, 0px)");
		} else {
			/////////// SHOW THE MENU //////////
			// request required info
			request_all_logins();
			request_all_rules();
			request_all_cams();
			request_all_areas();
			// show menu
			m.addClass("menu_active");

			var hamb=$("#hamb");
			// set the postition to be fixed to the div below
			hamb.css("position", "fixed");
			// move the hamb out, with the menu (same timing)
			hamb.css("transition","all 0.75s ease-in-out").css("transform", "translate("+(m.outerWidth(true)-$("#hamb").outerWidth()-20)+"px, 0px)");
			// and as soon as the animation is done, move it in the DOM into the menu object, so it will scroll with the menu
			setTimeout(function() { 
				var hamb=$("#hamb");
				hamb.detach();	// this will not only detach it but also remove the transform appearently
				m.append(hamb);
				hamb.off();
				hamb.click(function(){ toggle_menu(); });
			}, 760);

		};
	};
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function request_all_areas(){
	var cmd_data = { "cmd":"get_areas"};
	con.send(JSON.stringify(cmd_data));
	g_areas=[];
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function request_all_rules(){
	var cmd_data = { "cmd":"get_rules"};
	con.send(JSON.stringify(cmd_data));
	g_rules=[];
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function request_all_logins(){
	var cmd_data = { "cmd":"get_logins"};
	con.send(JSON.stringify(cmd_data));
	g_logins=[];
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function request_all_cams(){
	var cmd_data = { "cmd":"get_cams"};
	con.send(JSON.stringify(cmd_data));
	g_m2m=[];
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function parse_sidebar_info(msg){
	///////////////////////////////// Parse individual info and go one if all entries are set /////////////
	if(msg["cmd"]=="get_areas"){
		// save all areas as array in the global g_areas
		g_areas=[];
		for(var i=0;i<msg["areas"].length;i++){
			g_areas[i]=msg["areas"][i];
		};
	} else if(msg["cmd"]=="get_cams"){
		// save all cams as array 
		for(var i=0;i<msg["m2m"].length;i++){
			g_m2m[i]=msg["m2m"][i];
		};
	} else if(msg["cmd"]=="get_logins"){
		// save all logins as array 
		g_logins=[];
		for(var i=0;i<msg["m2m"].length;i++){
			g_logins[i]=msg["m2m"][i];
		};
	} else if(msg["cmd"]=="get_rules"){
		var i=0;
		g_rules=[];
		for(var a in msg["rules"]){
			g_rules[i]=msg["rules"][i+1];
			i++;
		};
	};
	///////////////////////////////// Parse individual info and go one if all entries are set /////////////

	if(g_areas.length && g_m2m.length && g_rules.length){
		/////////////////////// RM BOX ////////////////////
		var field=$("#rm_box");
		if(field.length){
			field.text("");
			// go through all areas
			for(var a=0;a<g_areas.length;a++){
				g_areas[a]["rules"]=[];
				g_areas[a]["subrules"]=[];
				// join rules and adreas
				for(var b=0;b<g_rules.length;b++){
					if(g_rules[b]["name"]==g_areas[a]["area"]){
						g_areas[a]["rules"]=g_rules[b]["rules"];
						g_areas[a]["subrules"]=g_rules[b]["subrules"];
					};
				};

				add_rm_entry(field,g_areas[a]);
			};
		};
		/////////////////////// RM BOX ////////////////////

		/////////////////////// AREAS BOX ////////////////////
		// add m2m count to each area
		for(var a=0;a<g_areas.length;a++){
			var c=0;
			for(var i=0; i<g_m2m.length; i++){
				if(g_m2m[i]["area"]==g_areas[a]["area"]){
					c++;
				}
			};
			g_areas[a]["m2m_count"]=c;
		};
			
		// start showing the areas
		var field=$("#areas_box");
		if(field.length){
			field.text("");
			for(var a=0;a<g_areas.length;a++){
				//onsole.log(g_areas[a]);
				add_area_entry(field,g_areas[a]);
			}
			// prepare vars for one empty new box
			m_area={};
			m_area["area"]="";				
			m_area["id"]="-1";
			m_area["latitude"]="52.479761";				
			m_area["longitude"]="62.185661";				
			m_area["m2m_count"]=0;				
			// run it one more time
			add_area_entry(field,m_area);
		}; // area box
		/////////////////////// AREAS BOX ////////////////////

		/////////////////////// CAMERA BOX ////////////////////
		// populate the camera box
		var field=$("#cameras_box");
		if(field.length){
			field.text("");
			for(var a=0;a<g_m2m.length;a++){
				add_camera_entry(g_m2m[a],field);
			}; // for each camera
		}; // camera box
		/////////////////////// CAMERA BOX ////////////////////

		/////////////////////// USER /////////////////////
		var field=$("#users_box");
		if(field.length){
			field.text("");
			for(var a=0; a<g_logins.length; a++){
				add_login_entry(field,g_logins[a]);
			}
			// add new entry to insert new entry
			var last=[];
			last["id"]=-1;
			add_login_entry(field,last);
			

		};
		/////////////////////// USER /////////////////////

	};
};

/////////////////////////////////////////// REMOVE AREA //////////////////////////////////////////
// triggered by: 	user click
// arguemnts:	 	id of area
// what it does: 	send msg to server
// why: 	 	clean account
/////////////////////////////////////////// REMOVE AREA //////////////////////////////////////////
function remove_area(id){
	var cmd_data = { "cmd":"remove_area", "id":id};
	console.log(cmd_data);
	con.send(JSON.stringify(cmd_data));
};

/////////////////////////////////////////// GIT_UPDATE //////////////////////////////////////////
// triggered by: 	user clicked on update button
// arguemnts:	 	mid of cam
// what it does: 	just forward it to the server
// why: 	 	to tritter the git update on the client side
/////////////////////////////////////////// GIT_UPDATE //////////////////////////////////////////
function git_update(mid){ 
	var cmd_data = { "cmd":"git_update", "mid":mid};
	console.log(cmd_data);
	con.send(JSON.stringify(cmd_data));
}

/////////////////////////////////////////// UPDATE_CAM_PARAMETER //////////////////////////////////////////
// triggered by: 	user changed values in sidebar for cam
// arguemnts:	 	mid of cam
// what it does: 	gathers all info for the cam and send it to the server
// why: 	 	to change cam behaviour
/////////////////////////////////////////// UPDATE_CAM_PARAMETER //////////////////////////////////////////
function update_cam_parameter(mid){
	var area=$("#"+mid+"_area_select");
	var qual=$("#"+mid+"_qual_select");
	var alarm_while_stream=$("#"+mid+"_alarm_while_stream_select");
	var fps=$("#"+mid+"_fps_select");
	
	if(area.length && qual.length && alarm_while_stream.length && fps.length){
		var cmd_data = { "cmd":"update_cam_parameter", "mid":mid, "area":area.val(), "qual":qual.val(), "alarm_while_stream":alarm_while_stream.val(), "fps":fps.val()};
		console.log(cmd_data);
		con.send(JSON.stringify(cmd_data));
	}
};

/////////////////////////////////////////// UPDATE_GEOFENCING //////////////////////////////////////////
// triggered by: 	user changed values in sidebar for geofencing
// arguemnts:	 	name of area + value for geofencing
// what it does: 	gathers all info for the cam and send it to the server
// why: 	 	to change rm behaviour
/////////////////////////////////////////// UPDATE_GEOFENCING //////////////////////////////////////////
function update_rule_geo(area_name,geo_fencing_on_off){
	var cmd_data = { "cmd":"update_rule_geo", "name":area_name, "geo":geo_fencing_on_off };
	console.log(cmd_data);
	con.send(JSON.stringify(cmd_data));
};

/////////////////////////////////////////// UPDATE_AREA //////////////////////////////////////////
// triggered by: 	user changed values in sidebar for area
// arguemnts:	 	id of area, name, longitude, latitude
// what it does: 	gathers all info for the area and send it to the server, close the maps view
// why: 	 	to change area info behaviour
/////////////////////////////////////////// UPDATE_AREA //////////////////////////////////////////
function update_area(id, name, latitude, longitude){
	var cmd_data = { "cmd":"update_area", "id":id, "name":name, "longitude":longitude, "latitude":latitude };
	console.log(cmd_data);
	con.send(JSON.stringify(cmd_data));
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function update_login(id,name,pw){
	// vertically and horizontally center box 
	txt2fb(get_loading("loading_welcome","Loading ..."));

	var cmd_data = { "cmd":"update_login", "id":id, "pw": CryptoJS.MD5(pw).toString(CryptoJS.enc.Hex), "name": name, "email":"qwe@qwe.qwe" };
	console.log(cmd_data);
	con.send(JSON.stringify(cmd_data));
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function remove_logins(id){
	var cmd_data = { "cmd":"remove_login", "id":id };
	console.log(cmd_data);
	con.send(JSON.stringify(cmd_data));
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////
function get_loading(id,text){
	//console.log("adding get loading");
	if(typeof(id) == "undefined"){
		id="loading_window";
	}
	if(typeof(text) == "undefined"){
		text="loading...";
	}

	//console.log("running it with:"+id+", "+text);

	var wrap=$("<div></div>");
	wrap.attr("id",id);
	wrap.addClass("loading");

	// text field
	var txt=$("<div></div>");
	txt.text(text);
	txt.addClass("loading");

	// preview image
	var img=$("<img></img>");
	img.attr({
		"src" : host+"images/support-loading.gif",
		"width":32,
		"height":32
	});

	wrap.append(txt);
	wrap.append(img);
	return wrap;
}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function resize_alert_pic(mid,data){
	var img=$("#"+mid+"_liveview_pic");
	var fb_inner=img.parent();
	var fb_outer=img.parent().parent().parent().parent();
	var w=$(window).width();
	var h=$(window).height();

	if(!img.parent().hasClass("fancybox-inner")){
		// if picture is open in the website, use dimensions of the m2m box
		var lv=$("#"+msg_dec["mid"]);
		var scale=lv.width()/1280;
		scale*=0.9;
 
		img.attr({
			"src":"data:image/jpeg;base64,"+msg_dec["img"],
			"width":(1280*scale),
			"height":(720*scale)
			//"style":" padding-top: 20px;" deactivated to have debug info nice and close the the image
		});

	} else {
		// if picture has been opened in the fancybox, adaopt size of fancybox	
		var scale=w/1280; // assume portait
		if(w/1280 > h/720){
			// e.g. 16:9 landscape 
			scale=h/720;
		}

		scale*=0.8;
		var img_w=1280*scale;
		var img_h=720*scale;
	

		img.attr({
			'width':img_w,
			'height':img_h,
			"style":" padding-top: 0px;"
		});

		fb_inner.attr({
			'style':'height='+(img_h+11)+'px'
		});

		var fb_w=img_w+40;
		var fb_h=img_h+31;
	
		fb_outer.attr({
			'style':
				'height='+fb_h+'px;'+
				'width: '+fb_w+'px;'+
				'position: fixed;'+
				'left: '+((w-fb_w)/2)+'px;'+
				'top: '+((h-fb_h)/2)+'px;'+
				'opacity: 1; overflow: visible;'
		});
	};

	// set new image
	if(data!=""){
		img.attr({
			"src":"data:image/jpeg;base64,"+data,
		});
	};

}

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function txt2fb(text){
	if(typeof(text)=="object"){
		text.find("div").addClass("loading_fb");
	};	
	var fb=$("<a></a>");
	fb.attr("id","txt2fb");
	fb.attr("style","text-align:left;");
	fb.html(text);
	fb.fancybox().trigger('click');
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function format_rm_status(text){
	//console.log("start formating");
	var s=["\r","\n","<r>","</r>","<g>","</g>","> <","</div>Sub-"];
	var r=["","","<div style='color:red'>","</div>","<br><div style='color:green'>","</div>","><","</div><br>Sub-"];
	for(i=0; i<s.length; i++){
		//console.log(text);
		//console.log("search for "+s[i]);
		while(text.indexOf(s[i])>=0){
			//console.log("hab eins");
			text=text.replace(s[i],r[i]);
		};
	};
	//console.log("returning:");
	//console.log(text);
	return '<div align="left">'+text+'</div>';
};

/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function show_alert_fb(mid){
	if(is_liveview_open(mid)){
		return;
	};
	// situation where we want this box:
	// 1.) user log fresh in an there is a running alarm
	// 2.) user was logged-in an there is a alarm starting but the liveview is still closed

	// generate text and a link to the alertview and display it as fancybox
	var disp=$("<div></div>");
	disp.attr("id",mid+"_liveview_alert_fb");
	var text=$("<div></div>").text("there is a camera in alert state!");
	disp.append(text);
	var button=$("<a></a>");
	button.text("stream");
	button.addClass("button");
	button.click(function(){
		return function(){
			event.stopPropagation();
			$.fancybox.close();				
	
			show_liveview(mid);
			$('html,body').animate({
				scrollTop: $("#"+mid+"_toggle_liveview").offset().top-($(window).height()/20)
			},1000);
		};
	}());
	disp.append(button);
	txt2fb(disp);	
	
};
/////////////////////////////////////////// UNSET //////////////////////////////////////////
// triggered by: eigther a alarm followed by a state change to idle, or a login: parse_msg
// arguemnts:	 MID and # of unacknowledged alarms
// what it does: prepares a textboxs and calls fancybox view with it
// why: 	 to give the user the info about an alert and the ability to review the data
/////////////////////////////////////////// UNSET //////////////////////////////////////////

function show_old_alert_fb(mid,open_alerts){
	if(open_alerts==0 || is_alarm_open(mid)){
		return;
	};

	// situation where we want this box:
	// 1.) user logs fresh in and there are open_alerts
	// 2.) user was logged-in and there was an alert (other fb still open) that was ignored 

	// generate text and a link to the alertview and display it as fancybox
	var nickname=$("#"+mid+"_name").text();
	var msg="Your safety is the top priority of illuminum <br><br>";
	msg+="The camera '"+nickname+"' has "+open_alerts+" unacknowledge alerts!<br>";
	msg+="Please confirm those alerts by clicking the acknowledge Button";


	var disp=$("<div></div>");
	disp.attr("id",mid+"_old_alerts");
	var text=$("<div></div>").html(msg);
	disp.append(text);
	var button=$("<a></a>");
	button.text("open alert-viewer");
	button.addClass("button");
	button.click(function(){
		return function(){
			event.stopPropagation();
			$.fancybox.close();				
	
			show_alarms(mid);
			get_alarms(mid,true);
			$('html,body').animate({
				scrollTop: $("#"+mid+"_toggle_alarms").offset().top-($(window).height()/20)
			},1000);
		};
	}());
	disp.append(button);
	txt2fb(disp);	
};

/////////////////////////////////////////// ADD LOGIN //////////////////////////////////////////
// triggered by: the connection beeing opened and no global login available, a false login, an empty submit
// arguemnts:	 an optional msg like "login failed"
// what it does: shows a login box and removes everything else
// why: 	 to enable the user manually to login
/////////////////////////////////////////// ADD LOGIN //////////////////////////////////////////

function add_login(msg){
	$("#welcome_loading").remove();
	$("#login_node").remove();
	$("#clients").html("");

	var node_wrap=$("<div></div>");
	node_wrap.addClass("center_hor");
	node_wrap.addClass("center");
	node_wrap.attr("id","login_node");

	var node=$("<div></div>");
	node.addClass("area_node");
	node_wrap.append(node);


	var dummy=$("<iframe></iframe");
	dummy.attr("src","index.php?useas=dummy");
	dummy.attr("name","dummy");
	dummy.attr("id","dummy");
	dummy.hide();	
	dummy.insertBefore($("#clients"));	

	var form=$("<form></form>");
	form.attr("methode","post");
	form.attr("target","dummy");
	form.attr("action"," ");
	form.attr("id","login_form");
	
	form.submit(function(){
		return function(){
			if($("#login_form").context.activeElement.value=="register"){
				show_register();				
			} else {
				if($("#pw").val()==""){
					$("#pw").focus();
					event.preventDefault();
				} else {
					send_login($("#login").val(),$("#pw").val());
				};
			};
		}
	}());		
	node.append(form);

	var container=$("<div></div>");
	form.append(container);

	var login_usr=$("<input></input>");
	login_usr.attr("id","login");
	login_usr.attr("type","text");
	login_usr.attr("autofocus","1");
	login_usr.addClass("clear_both");
	container.append(login_usr);

	var container=$("<div></div>");
	form.append(container);

	var login_pw=$("<input></input>");
	login_pw.attr("id","pw");
	login_pw.attr("type","password");
	container.append(login_pw);

	// needed to catch the ENTER-key
	var submit=$("<input></input>");
	submit.attr("type","submit").attr("value","login");
	form.append(submit);
	
	// and new register button
	submit=$("<input></input>");
	submit.attr("type","submit").attr("value","register");
	form.append(submit);
	
	var message=$("<div></div>");
	message.addClass("center");
	if(msg!=""){
		message.text(msg);
	};
	node.append(message);

	node_wrap.insertBefore($("#clients"));

};

/////////////////////////////////////////// SEND LOGIN //////////////////////////////////////////
// triggered by: the submission of the add_login form, or a reconnect if global user data are set or cordova login
// arguemnts:	 user and password as string
// what it does: send the data UNDCODED TODO
// why: 	 ...
/////////////////////////////////////////// SEND LOGIN //////////////////////////////////////////

function send_login(user,pw){
	$("#login_node").remove();	
	if((user=="" || pw=="") || (user=="nongoodlogin" && pw=="nongoodlogin")){	
		// empty form send
		add_login("please enter a user name and a password");
	} else {
		// store to reconnect without prompt
		g_user=user;
		g_pw=pw;

		// hash the password, combine it with the challange and submit the hash of the result
		var hash_pw = CryptoJS.MD5(pw).toString(CryptoJS.enc.Hex);
		var hash = CryptoJS.MD5(hash_pw+prelogin).toString(CryptoJS.enc.Hex);
		//console.log("received pw="+pw+" as hash="+hash_pw+" and prelogin="+prelogin+" and generated hash="+hash);
		var cmd_data = { "cmd":"login", "login":user, "client_pw":hash, "alarm_view":0};
		con.send(JSON.stringify(cmd_data)); 
		$("#welcome_loading").remove();
	
		// vertically and horizontally center box
		var l=$("<div></div>");
		l.addClass("center_hor").addClass("center").attr("id","welcome_loading");
		l.insertAfter("#clients");
		l.append(get_loading("wli","Login in..."));
	};
};

/////////////////////////////////////////// REQUEST PRE LOGIN //////////////////////////////////////////
// triggered by: on connection open
// arguemnts:	 none
// what it does: sends a message to the server to receive a randomized string that avoids repetition of passwords
// why: 	 to increase security
/////////////////////////////////////////// REQUEST PRE LOGIN //////////////////////////////////////////
function request_pre_login(){
	var cmd_data = { "cmd":"prelogin" };
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data)); 
};

function check_login_data(try_cordova){
	if(g_user=="nongoodlogin" || g_pw=="nongoodlogin" || g_user=="" || g_pw==""){
		if($("#login_node").length==0){
			add_login("");
		};
		if(try_cordova){
			c_autologin();
		};
	} else {
		send_login(g_user,g_pw);
	};
}


////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////// CORDOVA ///////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////
function c_set_login(user,pw){
	//console.log("setting data:"+user+"/"+pw);
	if(typeof cordova !== 'undefined'){
		cordova.exec(
			function(r){ 		/*alert("c_set_ok"); 	*/	},
			function(result){  	/*alert("Error return on GetUser - set data");*/	},
			"GetLogin",
			"set",
			[user,pw]
		);
	};
};

function c_autologin(){
	if(typeof cordova !== 'undefined'){
		$("#l10n_title").text("WOHOO CORDOVA GEFUNDEN");

		console.log("cordova exists");
		cordova.exec(
			function(r){ 
				console.log("r.l="+r.l+" r.p="+r.p+" r.q="+r.q);
				if(r.q!="" && r.l!="" && r.p!=""){
					if(r.q=="0"){
						console.log("Cordova autologin "+r.l+"/"+r.p);
						g_user=r.l;
						g_pw=r.p;
						check_login_data(0);
					};
				};
			},
			function(result){ /*alert("Get Login GET resultet in an error"); */ },
			"GetLogin",
			"get",
			[]
		);
	};
};


function c_set_callback(){
	if(typeof cordova !== 'undefined'){
		document.addEventListener("pause", c_freeze, false);
		document.addEventListener("resume", c_unfreeze, false);
	}
};

function c_freeze(){
		$("#l10n_title").text("freeeze");
		c_freeze_state=1;
		con.close();
};

function c_unfreeze(){
		$("#l10n_title").text("unfreeeze");
		if(c_freeze_state==1){
			// c_freeze_state=0; this will be done in the m2v_login method as we have to restore the camera 
			open_ws();
		};
}
	
/////////////////////////////////////////// SHOW FANCEBOX  //////////////////////////////////////////
// triggered by: show some messages
// arguemnts:	 content=html text, id=to be able to erase it
// why: 	 user interaction
/////////////////////////////////////////// SHOW FANCEBOX  //////////////////////////////////////////
function show_fancybox(content, id){
	// show fancybox
	var rl_msg = $("<div></div>").html(content);
	rl_msg.attr({
		"id":id,
	});
	var rl = $("<a></a>");
	rl.attr("href","#"+id);
	$(document.body).append(rl_msg);
	rl.fancybox({
		openEffect: 'none',
		closeEffect: 'none',
		helpers: {	overlay : {closeClick: false}	},
		closeBtn: false,   
		closeClick: false
	}).trigger('click');
}

/////////////////////////////////////////// show register  //////////////////////////////////////////
// triggered by: show some messages
// arguemnts:	 content=html text, id=to be able to erase it
// why: 	 user interaction
/////////////////////////////////////////// show register  //////////////////////////////////////////
function show_register(){
	// hier neues pw confirmen
	var text=$("<div></div>");
	var input=$("<input></input>");

	var form=$("<form></form>");
	form.attr("methode","post");
	form.attr("target","dummy");
	form.attr("action"," ");
	form.attr("id","register_form");

	form.submit(function(){
		return function(){
			var l_name=$("#l_name").val();
			var l_email=$("#l_email").val();
			var l_pw=$("#l_pw").val();
			var l_pw_conf=$("#l_pw_conf").val();
			var ok=1;
			var msg="Request send...";
		
			if(l_name==""){
				ok=0;
				msg="You have to enter a username";
			} else if(l_email==""){
				ok=0;
				msg="You have to enter a eMail adress, otherwise I can't send you evidence";
			} else if(l_pw=="" || l_pw_conf==""){
				ok=0;
				msg="You have to supply a password and confirm it";
			} else if(l_pw!=l_pw_conf){
				ok=0;
				msg="Your password don't match";
			}

			var hash_pw = CryptoJS.MD5(l_pw).toString(CryptoJS.enc.Hex);


			if(ok==1){
				var cmd_data = { "cmd":"new_register", "user":l_name, "email":l_email, "pw":hash_pw };
				con.send(JSON.stringify(cmd_data));
			};
			
			$("#register_msg").text(msg);
			event.preventDefault();
		}
	}());		


	text=$("<div></div>");
	text.html("Username:<br>");
	input=$("<input></input>");
	input.attr("id","l_name");
	input.val($("#login").val());
	form.append(text);				
	form.append(input);

	text=$("<div></div>");
	text.html("eMail:<br>");
	input=$("<input></input>");
	input.attr("id","l_email");
	form.append(text);				
	form.append(input);

	text=$("<div></div>");
	text.html("Password:<br>");
	input=$("<input></input>");
	input.val($("#pw").val());
	input.attr("id","l_pw");
	input.attr("type","password");
	form.append(text);				
	form.append(input);

	text=$("<div></div>");
	text.html("Confirm password:<br>");
	input=$("<input></input>");
	input.attr("id","l_pw_conf");
	input.attr("type","password");
	form.append(text);				
	form.append(input);

	var submit=$("<input></input>");
	submit.attr("type","submit").attr("value","register");
	text=$("<div></div>");
	text.attr("id","register_msg");
	text.html("");
	form.append(submit);
	form.append(text);
				
	show_fancybox(form,"register_input_box");
}

/////////////////////////////////////////// callback register  //////////////////////////////////////////
// triggered by: incoming msg from the websocket
// arguemnts:	 value = status for the SQL query, 0=good, -2=user exists already, -1=exception in sql 
// why: 	 
/////////////////////////////////////////// callback register  //////////////////////////////////////////
function callback_register(value){
	var msg="Registration successful, login in 3 sec"
	var ok=1;
	if(value==-2){
		msg="Sorry that name is taken";
		ok=0;
	} else if(value!=0){
		msg="Unknown return value "+value;
		ok=0;
	}
	$("#register_msg").text(msg);

	if(ok==1){
		var login=$("#l_name").val();
		var pw=$("#l_pw").val();
		setTimeout(function() { $("#register_input_box").remove();}, 3000);
		setTimeout("$.fancybox.close()",3000);
		console.log("send:"+login+","+pw);
		setTimeout(send_login,3000,login,pw);		
	};
};

/////////////////////////////////////////// set override buttons  //////////////////////////////////////////
// triggered by: incoming msg from the websocket at login or change of settings
// arguemnts:	 account and area of the cam, status of the override ("*","/","")
// why: 	 
/////////////////////////////////////////// callback register  //////////////////////////////////////////
function set_override_buttons(account, area, value){
	var on=$("#"+account+"_"+area+"_on");
	var off=$("#"+account+"_"+area+"_off");
	var auto=$("#"+account+"_"+area+"_auto");

	if(auto.length && on.length && off.length && value !== undefined){
		// remove all old handles
		auto.off();
		on.off();
		off.off();

		// auto
		auto.click(function(){
			var acc_int=account;
			var area_int=area;
			return function(){
				set_override(acc_int,area_int,"");
			}
		}());

		// off
		off.click(function(){
			var acc_int=account;
			var area_int=area;
			return function(){
				set_override(acc_int,area_int,"/");
			}
		}());

		// on
		on.click(function(){
			var acc_int=account;
			var area_int=area;
			return function(){
				set_override(acc_int,area_int,"*");
			}
		}());

		// colorize
		on.removeClass("button_selected");
		on.removeClass("button_deactivated");
		off.removeClass("button_selected");
		off.removeClass("button_deactivated");
		auto.removeClass("button_selected");
		auto.removeClass("button_deactivated");

		if(value==""){
			auto.addClass("button_selected");
		} else if(value=="*"){
			on.addClass("button_selected");
		} else if(value=="/"){
			off.addClass("button_selected");
		} 
	};	

};

/////////////////////////////////////////// show Map  //////////////////////////////////////////
// triggered by: 	user klick
// arguemnts:		lat, lng are start coordinates, map-,lat-,lng-ele are the outputs
// why: 	 	map shall provide coordinates for area
/////////////////////////////////////////// show Map  //////////////////////////////////////////
function show_map(lat,lng,map_ele,lat_ele,lng_ele){
        var map;
        var geocoder;
        var marker;
        var infowindow;

        var latlng = new google.maps.LatLng(lat,lng);
        var myOptions = {
            zoom: 9,
            center: latlng,
            panControl: true,
            scrollwheel: false,
            scaleControl: true,
            overviewMapControl: true,
            overviewMapControlOptions: { opened: true },
            mapTypeId: google.maps.MapTypeId.HYBRID
        };
        map = new google.maps.Map(map_ele[0],myOptions);
        geocoder = new google.maps.Geocoder();
        marker = new google.maps.Marker({
            position: latlng,
            map: map
        });

        map.streetViewControl = false;

        google.maps.event.addListener(map, 'click', function(event) {
            marker.setPosition(event.latLng);
            lat_ele.val(event.latLng.lat().toFixed(6));
            lng_ele.val(event.latLng.lng().toFixed(6));
	});
};
