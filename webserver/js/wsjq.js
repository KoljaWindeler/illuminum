// connection
var con = null;
//var IP="52.24.157.229";
var IP="illuminum.speedoino.de";
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


// run as son as everything is loaded
$(function(){
	c_set_callback();
	var l=$("<div></div>");
	l.addClass("center_hor").addClass("center").attr("id","welcome_loading");
	l.insertAfter("#clients");
	l.append(get_loading("wli","Connecting..."));
	
	add_menu();
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
		};
		c_set_login(g_user,g_pw);
		setTimeout("$('#wli').addClass('loginok')",1000);
		setTimeout("$('#wli').html('Login accepted, all your cameras will show up.<br>You can also register new cameras now.')",1000);
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
//		txt.text("Movement detected at: "+a.getDate()+"."+(a.getMonth()+1)+"."+a.getFullYear()+" "+hour+":"+min);
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
// what it does: create an area and a m2m if it does not exists. 
// why: 	 core code for the interface
/////////////////////////////////////////// CHECK_APPEND_M2M //////////////////////////////////////////

function check_append_m2m(msg_dec){
	//console.log(msg_dec);
	// get root clients node
	if($("#clients").length){
		//console.log("suche nach gruppe "+msg_dec["account"]+"_"+msg_dec["area"]);
		var area=$("#"+msg_dec["account"]+"_"+msg_dec["area"]);
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

			var button=document.createElement("A");
			button.setAttribute("id",msg_dec["account"]+"_"+msg_dec["area"]+"_on");
			button.className="button";
			button.text="Force Detection on";
			button.onclick=function(){
				var msg_int=msg_dec;
				return function(){
					set_override(msg_int["account"],msg_int["area"],"*");
				}
			}();
			header_button.append(button);

			button=document.createElement("A");
			button.setAttribute("id",msg_dec["account"]+"_"+msg_dec["area"]+"_off");
			button.onclick=function(){
				var msg_int=msg_dec;
				return function(){
					set_override(msg_int["account"],msg_int["area"],"/");
				}
			}();
			button.className="button";
			button.text="Force Detection off";
			header_button.append(button);

			$("#clients").append(node);
			area=node;
			/////////////////// CREATE AREA ////////////////////////////(
		} // area
	} // clients

	var mid=msg_dec["mid"];
	var node=$("#"+mid);
	// check if this m2m already exists
	if(!node.length){
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
	//	m2m_header_text.append(glow);
	

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

		// add fps dropdown
		var fps_select=$("<select></select>");
		fps_select.attr({
			"id": mid+"_fps_select",
			"class":"setup_controll_scroller"
		});
		// load from message
		var default_t=parseFloat(msg_dec["frame_dist"]);
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
		setupcontrol.append(fps_select);

		// quality selector
		var qual_select=$("<select></select>");
		qual_select.attr({
			"id": mid+"_qual_select",
			"class":"setup_controll_scroller"
		});
		qual_select.append($('<option></option>').val("HD").html("HD resolution, slow").prop('selected', true));
		qual_select.append($('<option></option>').val("VGA").html("VGA resolution, fast"));
		setupcontrol.append(qual_select);

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
	} // node
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
		set_interval(mid,0,0);
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

		// load fps from input
		var fps=0.5;
		var qual=1; // 1 high, 0 low
		var fps_sel=$("#"+mid+"_fps_select");
		var qual_sel=$("#"+mid+"_qual_select");
		if(fps_sel.length){
			fps=fps_sel.val();
		};
		if(qual_sel.length){
			qual=qual_sel.val();
		};

		// send request
		set_interval(mid,fps,qual);
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

function set_interval(mid,interval,qual){
	if(con == null){
		return;
	}
	var cmd_data = { "cmd":"set_interval", "mid":mid, "interval":interval, "qual":qual};
	con.send(JSON.stringify(cmd_data));

	// active / deactivate fast HB, updates once per second
	if(interval==0){
		cmd_data = { "cmd":"hb_fast", "active":0};
	} else {
		cmd_data = { "cmd":"hb_fast", "active":1};
	}
	con.send(JSON.stringify(cmd_data));

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
	if(detection>0){
		$("#"+account+"_"+area+"_on").hide();
		$("#"+account+"_"+area+"_off").show();
	} else {
		$("#"+account+"_"+area+"_on").show();
		$("#"+account+"_"+area+"_off").hide();
	};
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
			show_old_alert_fb(mid,-1);
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

function add_menu(){
	/******* add menu ******/
	// menu itsself
	var menu=$("<div></div>");
	menu.attr("id","menu");
	menu.addClass("menu");
	var list=$("<ul></ul>");
	
	var listentry=$("<li></li>");
	listentry.text("Log out");
	listentry.click(function(){
		return function(){
			g_user="nongoodlogin";
			g_pw="nongoodlogin";
			c_set_login(g_user,g_pw);
			txt2fb(get_loading("","Signing you out..."));
			fast_reconnect=1;
			con.close();

			// hide menu
			var m=$("#menu");
			if(m.length){
				if(m.hasClass("menu_active")){
					m.removeClass("menu_active");
					$("#hamb").css("position", "absolute");
					$("#hamb").css("transform", "translate(0px, 0px)");
					$("#hamb").css("transition","all 0.75s ease-in-out");
				}
			}
		}
	}());
	list.append(listentry);

	listentry=$("<li></li>");
	var t=$("<div></div>");
	t.attr("id","HB_fast");
	t.text("hb_fast");
	listentry.append(t);
	list.append(listentry);


	menu.append(list);
	menu.insertAfter("#clients");
	

	var header=$("<header></header>");
	header.click(function(){
		return function(){
			var m=$("#menu");
			if(m.length){
				if(m.hasClass("menu_active")){
					m.removeClass("menu_active");
					$("#hamb").css("position", "absolute");
					$("#hamb").css("transform", "translate(0px, 0px)");
					$("#hamb").css("transition","all 0.75s ease-in-out");
				} else {
					m.addClass("menu_active");
					$("#hamb").css("position", "fixed");
					$("#hamb").css("transform", "translate("+(m.outerWidth(true)-$("#hamb").outerWidth()-20)+"px, 0px)");
					$("#hamb").css("transition","all 0.75s ease-in-out");
				};
			};
		};
	}());
	var hamb=$("<div></div>");
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
	header.append(hamb);
	header.insertAfter("#clients");
	/******* add menu ******/
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
				send_login($("#login").val(),$("#pw").val());
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

