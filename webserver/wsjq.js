var con = null;
var f_t= 0;
var c_t=0;
var host="https://52.24.157.229/illumino/";

// run as son as everything is loaded
$(function(){
	var container=get_loading("welcome_loading","Loading your cameras ...");
	container.insertAfter("#clients");

	add_menu();
	open_ws();

	//var txt=$("<div></div>");
	//txt.html("-->"+$(window).width()+"/"+$(window).height()+"<--");
	//$("#clients").append(txt);	
});


// triggered by the ondocument_ready
function open_ws() {
	con = new WebSocket('wss://52.24.157.229:9879/');
	con.onopen = function(){
		if($("#rl_msg").length){
			$.fancybox.close();							
		};

		console.log("onOpen");
		login("browser","hui");
	};

	// reacting on incoming messages
	con.onmessage = function(msg) {
		console.log(msg);
		msg_dec=JSON.parse(msg.data);
		parse_msg(msg_dec);
	};
	con.onclose = function(){
		console.log("onClose");
		
		// show fancybox
		var rl_msg = $("<div></div>").text("onClose event captured,reconnect started");
		rl_msg.attr({
			"id":"rl_msg",
			"style":"display:none;width:500px;"
		});
		var rl = $("<a></a>");
		rl.attr("href","#rl_msg");
		$(document.body).append(rl_msg);
		rl.fancybox({
			openEffect: 'none',
			closeEffect: 'none',
			helpers: {	overlay : {closeClick: false}	},
			closeBtn: false,   
			closeClick: false
		}).trigger('click');
	
		setTimeout(open_ws(), 3000);
	};
};


// on message will call this function
function parse_msg(msg_dec){
	var mid=msg_dec["mid"];

	// server has established a connection between m2m and WS, this should be received after a login
	if(msg_dec["cmd"]=="m2v_login"){
		//console.log("m2v_lgogin detected:"+msg_dec);

		// check if m2m is already visible, if not append it. Then update the state and timestamp
		check_append_m2m(msg_dec);
		update_hb(msg_dec["mid"],msg_dec["last_seen"]);
		update_state(msg_dec["account"],msg_dec["area"],msg_dec["mid"],msg_dec["state"],msg_dec["detection"],msg_dec["rm"]);

		// remove loading if still existing and scroll down to the box 
		if($("#welcome_loading").length){
			$("#welcome_loading").remove();
			$('html,body').animate({
				scrollTop: $("#clients").offset().top-($(window).height()/20)
			},1000);
		};

	}

	// update the timestamp, we should receive this every once in a while
	else if(msg_dec["cmd"]=="hb_m2m"){
		update_hb(msg_dec["mid"],msg_dec["last_seen"]);
	}

	// update the state, we only receive that if a box changes its state. E.g. to alarm or to disarm
	else if(msg_dec["cmd"]=="state_change"){
		update_state(msg_dec["account"],msg_dec["area"],msg_dec["mid"],msg_dec["state"],msg_dec["detection"],msg_dec["rm"]);
	}

	// show a picture, we'll receive this because we requested it. Alarm will not send us pictures directly
	// this is a little different than the "requested_file" because we can't know the filename up front
	else if(msg_dec["cmd"]=="rf"){
		show_liveview_img(msg_dec);
	}

	// an m2m unit disconnects
	else if(msg_dec["cmd"]=="disconnect"){
		update_state(msg_dec["account"],msg_dec["area"],msg_dec["mid"],-1,msg_dec["detection"],"");
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

	// updated count of alerts, show correct button style and maybe close the popup
	else if(msg_dec["cmd"]=="update_open_alerts"){
		var button=$("#"+mid+"_toggle_alarms");
		var txt=$("#"+mid+"_toggle_alarms_text");
		set_alert_button_state(button,txt,msg_dec["open_alarms"]);

		// close msg about open alarms if someone already acknowledged them
		if($("#"+mid+"_old_alerts").length && msg_dec["open_alarms"]==0){
			event.stopPropagation();
			$.fancybox.close();				
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
	// debug calc delay
		/*
		var delay=parseInt(Date.now()-(1000*parseFloat(msg_dec["ts"])));
		if(delay>999){
			delay=999;
		};
		c_t=c_t+1;
		if(f_t==0){
			f_t=Date.now();
		}
		var fps=Math.floor((c_t/((Date.now()-f_t)/1000)*100))/100;
		$("#"+msg_dec["mid"]+"_hb").innerHTML="Foto age "+delay+" ms, fps: "+fps;
		*/

	// hide loading dialog, if there is one
	var txt=$("#"+msg_dec["mid"]+"_liveview_txt");
	if(txt.length){
		txt.hide();
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
	console.log("ids_closed:"+ids_closed.length);

	// remove loading it and add a ack all button
	var closed_disp=$("#"+mid+"_alarms_closed_display");
	var open_disp=$("#"+mid+"_alarms_open_display");

	var ids_open_old=$("#"+mid+"_alarms_open_list").text().split(",");
	var ids_closed_old=$("#"+mid+"_alarms_closed_list").text().split(",");

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
	var ids=	 [ids_open,			ids_closed];
	var old_ids=	 [ids_open_old,			ids_closed_old];
	var navigation=  [open_navi,			closed_navi];

	for(i=0; i<2; i++){
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
			console.log("no change, no action");
			continue;
		} else {
			// check if it is nearly the same, just one new entry up front
			console.log("ids_old="+old_ids[i]);
			console.log("ids_new="+ids[i]);
			console.log(ids[i][0]);
			console.log(old_ids[i][0]);
			console.log("length="+ids[i].length);
			var one_new_in_front=true;
			for(j=0; j<old_ids[i].length-1; j++){
				if(old_ids[i][j]!=ids[i][j+1]){
					one_new_in_front=false;
				}
			}
			if(!(one_new_in_front && old_ids[i].length>1)){ // due to split the length is 1 even for a empty chain
				// start all over
				disp[i].text("");
				console.log("restart");
			} else {
				console.log("no restart");
			}
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

		if(!(one_new_in_front && old_ids[i].length>1)){ // due to split the length is 1 even for a empty old array
			//request all
			// add per element one line 
			for(var j=0;j<ids[i].length;j++){		
				add_alert(ids[i][j],mid,disp[i]);
			};
			
			// request details	
			for(var j=0;j<ids[i].length;j++){
				var cmd_data = { "cmd":"get_alarm_details", "id":ids[i][j], "mid":mid};
				console.log(JSON.stringify(cmd_data));
				con.send(JSON.stringify(cmd_data)); 
			};
		} else {
			// we just have one new entry

			// insert a helper to reroute the anchor for 'add_alert()'
			var alert_helper=$("<div></div>");
			alert_helper.attr({
				"id":"alert_helper_"+mid+"_"+ids[i][0],
			});
			alert_helper.insertBefore($("#alert_"+mid+"_"+ids[i][1]));
			add_alert(ids[i][0],mid,alert_helper);
			
			
			// only request the one in the front
			var cmd_data = { "cmd":"get_alarm_details", "id":ids[i][0], "mid":mid};
			console.log(JSON.stringify(cmd_data));
			con.send(JSON.stringify(cmd_data)); 			
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
	console.log("ack for id:"+id);
	// remove field
	$("#alert_"+mid+"_"+id).fadeOut(600, function() { $(this).remove(); });

	// decrement nr
	var button=$("#"+mid+"_toggle_alarms");
	var open_alarms=parseInt(button.text().substring(0,button.text().indexOf(" ")))-1;
	var txt=$("#"+mid+"_toggle_alarms_text");
	set_alert_button_state(button,txt,open_alarms);

	var cmd_data = { "cmd":"ack_alert", "mid":mid, "aid":id};
	console.log(JSON.stringify(cmd_data));
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
	console.log(JSON.stringify(cmd_data));
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
					set_detection(msg_int["account"],msg_int["area"],"*");
				}
			}();
			header_button.append(button);

			button=document.createElement("A");
			button.setAttribute("id",msg_dec["account"]+"_"+msg_dec["area"]+"_off");
			button.onclick=function(){
				var msg_int=msg_dec;
				return function(){
					set_detection(msg_int["account"],msg_int["area"],"/");
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

	var node=$("#"+msg_dec["mid"]);
	// check if this m2m already exists
	if(!node.length){
		/////////////////// CREATE M2M ////////////////////////////(
		//console.log("knoten! nicht gefunden, lege ihn an");
		node=$("<div></div>");
		node.attr({
			"id":msg_dec["mid"],
			"class":"area_m2m"
		});
	
		var m2m_header=$("<div></div>");
		m2m_header.attr({
			"id":msg_dec["mid"]+"_header",
			"class":"m2m_header"
		});
		node.append(m2m_header);

		var icon=$("<img></img>");
		icon.attr({
			"id": msg_dec["mid"]+"_icon",
			"width": 64,
			"height": 51,
			"class":"m2m_header"
			});
		icon.addClass("cam_sym");
		m2m_header.append(icon);

		var m2m_header_text=$("<div></div>");
		m2m_header_text.attr({
			"id":msg_dec["mid"]+"_header_text",
			"class":"m2m_header_text"
		});
		m2m_header.append(m2m_header_text);
	
		var text=$("<div></div>").text(msg_dec["alias"]);
		text.attr({
			"id" : msg_dec["mid"]+"_name",
			"class": "m2m_text_name"
		});
		m2m_header_text.append(text);
		
		var glow=$("<div></div>");
		glow.attr("id",msg_dec["mid"]+"_glow");
		glow.addClass("glow_dot"); // setting real state in update routine
		glow.addClass("float_left");
		m2m_header_text.append(glow);

		text=$("<div></div>");
		text.attr({
			"id" : msg_dec["mid"]+"_state",
			"class": "m2m_text"
		});
		text.addClass("float_left");
		m2m_header_text.append(text);


		text=$("<div></div>").text("--");
		text.attr({
			"id" : msg_dec["mid"]+"_lastseen",
			"class": "m2m_text"
		});
		text.addClass("clear_both");
		m2m_header_text.append(text);

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
		button.text("glubsch!");
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
		wl.attr("id",msg_dec["mid"]+"_toggle_liveview_text");
		wl.addClass("toggle_liveview_text");
		wl.addClass("toggle_text");
		wb.append(wl);
		m2m_header_button.append(wb);
		//m2m_header_button.append(button);
		//////////// live view button /////////////
		
		//////////// light controll button /////////////
		wb=$("<div></div>");
		wb.addClass("inline_block");
		button=$("<a></a>");
		button.attr({
			"id": msg_dec["mid"]+"_toggle_lightcontrol",
		});
		button.addClass("color_sym");
		button.click(function(){
			var msg_int=msg_dec;
			return function(){
				toggle_lightcontrol(msg_int["mid"]);
			};
		}());
		button.text("color");
		set_button_state(button,msg_dec["state"]);
		wb.append(button);
		wl=$("<div></div>");
		wl.attr("id",msg_dec["mid"]+"_toggle_lightcontrol_text");
		wl.addClass("toggle_lightcontrol_text");
		wl.addClass("toggle_text");
		wb.append(wl);
		m2m_header_button.append(wb);
		//m2m_header_button.append(button);
		//////////// light controll button /////////////

		//////////// alert button /////////////
		wb=$("<div></div>");
		wb.addClass("inline_block");
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
		wl.attr("id",msg_dec["mid"]+"_toggle_alarms_text");
		wl.addClass("toggle_text");		// size etc
		wl.addClass("toggle_alarms_text");	// color and text
		wb.append(wl);
		m2m_header_button.append(wb);

		// hide it if no alarm is available
		set_alert_button_state(button,wl,msg_dec["open_alarms"]);
		//////////// alert button /////////////



		////////////////// LIVE VIEW ////////////////////////////
		liveview=$("<div></div>");
		liveview.attr({
			"id" : msg_dec["mid"]+"_liveview",
		});
		liveview.addClass("center");
		liveview.hide();
		node.append(liveview);

		var txt=$("<div></div>");
		txt.attr("id",msg_dec["mid"]+"_liveview_txt");
		txt.attr("style","padding-top:20px;");
		txt.html("Loading liveview<br>");
		liveview.append(txt);

		// fancybox link around the liveview
		var rl = $("<a></a>");
		rl.attr("href","#"+msg_dec["mid"]+"_liveview_pic");
		rl.fancybox({
			beforeShow: function() { 
				mid=msg_dec["mid"]; 
				resize_alert_pic(mid,""); 
			}
		});
		liveview.append(rl);

		var img=$("<img></img>");
		img.attr({
			"src" : host+"images/support-loading.gif",
			"id" : msg_dec["mid"]+"_liveview_pic",
			"width":64,
			"height":64
		});
		rl.append(img);
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
		scroller.addClass("light_controll_color");
		lightcontrol.append(scroller);

		scroller=$("<div></div>");
		scroller.attr({
			"id":"colorslider_"+msg_dec["mid"],
			"class":"light_controll_scroller"
		});
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
		scroller.addClass("light_controll_color");
		lightcontrol.append(scroller);

		scroller=$("<div></div>");
		scroller.attr({
			"id":"brightnessslider_"+msg_dec["mid"],
			"class":"light_controll_scroller"
		});
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
		alarms=$("<div></div>");
		alarms.attr({
			"id" : msg_dec["mid"]+"_alarms",
		});


		var open=$("<div></div>").attr("id",msg_dec["mid"]+"_alarms_open");
		open.append($("<div></div>").text("Not-acknowledged").addClass("m2m_text").addClass("inline_block"));
		open.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_open_navigation").text("Navigation").addClass("m2m_text").addClass("alert_navigation"));
		open.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_open_display"));
		open.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_open_list").hide());
		open.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_open_start").text("0").hide());
		open.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_open_count").text("10").hide());
		open.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_open_max").hide());
		alarms.append(open);	

		alarms.append($("<hr>"));

		var close=$("<div></div>").attr("id",msg_dec["mid"]+"_alarms_closed");
		close.append($("<div></div>").text("Acknowledged").addClass("m2m_text").addClass("inline_block"));
		close.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_closed_navigation").text("Navigation").addClass("m2m_text").addClass("alert_navigation"));
		close.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_closed_display"));
		close.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_closed_list").hide());
		close.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_closed_start").text("0").hide());
		close.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_closed_count").text("10").hide());
		close.append($("<div></div>").attr("id",msg_dec["mid"]+"_alarms_closed_max").hide());
		alarms.append(close);	

		alarms.hide();
		node.append(alarms);
		////////////////// ALARM MANAGER ////////////////////////////
		//<div style="width: 300px;" id="slider1"></div>


		area.append(node);
		//console.log("hb feld in client angebaut");
		/////////////////// CREATE M2M ////////////////////////////(
	} // node
	update_state(msg_dec["account"],msg_dec["area"],msg_dec["mid"],msg_dec["state"],msg_dec["detection"],msg_dec["rm"]);
	show_old_alert_fb(msg_dec["mid"],msg_dec["open_alarms"]);
}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function set_button_state(b,state){
	if(state==-1 && b.length){
		b.addClass("button_deactivated"); // avoids clickability
	};
};

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
function toggle_liveview(mid){
	if(is_button_active("#"+mid+"_toggle_liveview")){
		return;
	};

	if(is_liveview_open(mid)){
		hide_liveview(mid);
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

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function hide_liveview(mid){
	var view = $("#"+mid+"_liveview");
	$("#"+mid+"_toggle_liveview").removeClass("live_sym_active");
	if(view.is(":visible")){
		set_interval(mid,0);
		view.fadeOut("fast");
	}
}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function show_liveview(mid){
	hide_lightcontrol(mid);
	hide_alarms(mid);
	// set button active
	$("#"+mid+"_toggle_liveview").addClass("live_sym_active");
	var view = $("#"+mid+"_liveview");
	if(!view.is(":visible")){
		var img=$("#"+mid+"_liveview_pic");		
		img.attr({
			"src":host+"images/support-loading.gif",
			"width":64,
			"height":64
		});
		var txt=$("#"+msg_dec["mid"]+"_liveview_txt");		
		txt.show();

		view.fadeIn("fast");
		
		set_interval(mid,1);
	};
}
///////////////////////// LIVE VIEW //////////////////////////////////

///////////////////////////////////////////// COLOR VIEW /////////////////////////////////////////
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
function toggle_lightcontrol(mid){
	if(is_button_active("#"+mid+"_toggle_lightcontrol")){
		return;
	};

	var view = $("#"+mid+"_lightcontrol");
	if(view.is(":visible")){
		hide_lightcontrol(mid);
	} else {
		show_lightcontrol(mid);
	};
};

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function hide_lightcontrol(mid){
	var view = $("#"+mid+"_lightcontrol");
	$("#"+mid+"_toggle_lightcontrol").removeClass("color_sym_active");
	if(view.is(":visible")){
		view.fadeOut("fast");
	}
}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function show_lightcontrol(mid){
	hide_liveview(mid);
	hide_alarms(mid);
	$("#"+mid+"_toggle_lightcontrol").addClass("color_sym_active");
	var view = $("#"+mid+"_lightcontrol");
	if(!view.is(":visible")){
		view.fadeIn("fast");
	};
}
///////////////////////// COLOR VIEW //////////////////////////////////

///////////////////////// ALARM VIEW //////////////////////////////////
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function is_alarm_open(mid){
	var view = $("#"+mid+"_alarms");
	if(view.is(":visible")){
		return true;
	} else {
		return false;
	};	
};

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function hide_alarms(mid){
	var view = $("#"+mid+"_alarms");
	$("#"+mid+"_toggle_alarms").removeClass("alarm_sym_active");
	if(view.is(":visible")){
		view.fadeOut("fast");
	}
}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function show_alarms(mid){
	hide_lightcontrol(mid);
	hide_liveview(mid);
	$("#"+mid+"_toggle_alarms").addClass("alarm_sym_active");

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

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function set_alert_button_state(button,txt,open_alarms){
	if(open_alarms==0){
		button.text("no alarms");
		//button.addClass("button_deactivated"); // avoids clickability // we want it to be clickable
		button.addClass("alarm_sym_deactivated");
		button.removeClass("alarm_sym_active");
	} else if(open_alarms==1) {
		button.text(open_alarms+" alarm");
		button.addClass("alarm_sym");
		button.removeClass("alarm_sym_deactivated");
	} else {
		button.text(open_alarms+" alarms");
		button.addClass("alarm_sym");
		button.removeClass("alarm_sym_deactivated");
	}


	if(open_alarms==0){
		txt.addClass("sym_text_deactivated");
		txt.removeClass("toggle_alarms_text_active");
	} else {
		txt.addClass("toggle_alarms_text_active");
		txt.removeClass("sym_text_deactivated");
	}
}		
///////////////////////// ALARM VIEW //////////////////////////////////

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function state2glow(b,state,det){
	b.removeClass("glow_red");
	b.removeClass("glow_purple");
	b.removeClass("glow_green");

	if(state==-1){ //disconnected
		b.addClass("glow_red");
	} else if(state==1 && det>0){
		b.addClass("glow_purple");
	} else {
		b.addClass("glow_green");
	};
};

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function state2str(state,det){
	var ret="";
	if(state==0){
		ret = "idle";
	} else if(state==1){
		ret = "movement!";
	} else if(state==-1){
		ret = "disconnected";
	} else if(state==-2){ 
		// just show state
	} else {
		ret = state.toString();
	};

	if(state!=-1){
		if(state!=-2){
			ret += " | ";
		};
		if(det==0){
			ret += "Not protected";
		} else if(det==1){
			ret += "Protected";
		} else if(det==2){
			ret += "Very protected";
		} else {
			ret += det.toString();
		}
	};
	return ret;
}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function updateInfo(color) {
	var cmd_data = { "cmd":"set_color", "r":parseInt(parseFloat(color.rgb[0])*100), "g":parseInt(parseFloat(color.rgb[1])*100), "b":parseInt(parseFloat(color.rgb[2])*100)};
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
};	

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function set_interval(mid,interval){
	if(con == null){
		return;
	}
	var cmd_data = { "cmd":"set_interval", "mid":mid, "interval":interval};
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function login(user,pw) {
	console.log("send login");
	if(con == null){
		return;
	}
	var cmd_data = { "cmd":"login", "login":user, "client_pw":pw, "alarm_view":0};
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function set_detection(user,area,on_off){
	if(con == null) {
		return;
	}
	var cmd_data = { "cmd":"set_override", "rule":on_off, "area":area, "duration":"0"};
	console.log(JSON.stringify(cmd_data));
	con.send(JSON.stringify(cmd_data));
}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function update_state(account,area,mid,state,detection,rm){
	//console.log("running update state on "+mid+"/"+state);

	// set the rulemanager text explainaition
	$("#"+account+"_"+area+"_status").click(function(){
		var rm_int=rm;
		return function(){
			txt2fb(format_rm_status(rm_int));
		};
	}());
	// set the rulemanager text explainaition

	// text state of the m2m
	var e=$("#"+mid+"_state");
	if(e.length){
		e.text(state2str(state,detection));
	}
	// text state of the m2m

	// text state of the area
	e=$("#"+account+"_"+area+"_status");
	if(e.length){
		e.text(state2str(-2,detection));
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
	if(detection>0 && state>0){
	 	// if we change to alert-state, show popup with shortcut to the liveview
		show_alert_fb(mid);
	} else {
		// if we change to non-alert-state and there is still the alert popup, show the old_alert popup
		if($("#"+mid+"_liveview_alert_fb").length){
			show_old_alert_fb(mid,-1);
		};
	}
	// POP UP
	
	// make buttons available/unavailable
	var lv=$("#"+mid+"_toggle_liveview");
	var cv=$("#"+mid+"_toggle_lightcontrol");
	var av=$("#"+mid+"_toggle_alarms");
	var lt=$("#"+mid+"_toggle_liveview_text");
	var ct=$("#"+mid+"_toggle_lightcontrol_text");
	var at=$("#"+mid+"_toggle_alarms_text");
	if(state<0){
		lv.addClass("button_deactivated"); // avoids clickability
		lv.addClass("live_sym_deactivated");
		lv.removeClass("live_sym");
		lt.addClass("sym_text_deactivated");
		lt.removeClass("toggle_liveview_text_active");
	
		cv.addClass("button_deactivated"); // avoids clickability
		cv.addClass("color_sym_deactivated");
		cv.removeClass("color_sym");
		ct.addClass("sym_text_deactivated");
		ct.removeClass("toggle_lightcontrol_text_active");

		hide_liveview(mid);
		hide_lightcontrol(mid);
		//hide_alarms(mid); // alerts button will be shown/hidden by set_alarm .. something something
	} else {
		lv.removeClass("button_deactivated");
		lv.removeClass("live_sym_deactivated");
		lv.addClass("live_sym");		
		lt.removeClass("sym_text_deactivated");
		lt.addClass("toggle_liveview_text_active");

		cv.removeClass("button_deactivated");
		cv.removeClass("color_sym_deactivated");
		cv.addClass("color_sym");
		ct.removeClass("sym_text_deactivated");
		ct.addClass("toggle_lightcontrol_text_active");
	}
	// make buttons available/unavailable

}

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function add_menu(){
	/******* add menu ******/
	// menu itsself
	var menu=$("<div></div>");
	menu.attr("id","menu");
	menu.addClass("menu");
	var list=$("<ul></ul>");
	var listentry=$("<li></li>");
	listentry.text("test");
	list.append(listentry);
	menu.append(list);
	menu.insertAfter("#clients");
	

	var header=$("<header></header>");
	header.click(function(){
		return function(){
			console.log("suche nach menu");
			var m=$("#menu");
			if(m.length){
				console.log("menu gefunden");
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

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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
		scale*=0.8;
 
		img.attr({
			"src":"data:image/jpeg;base64,"+msg_dec["img"],
			"width":(1280*scale),
			"height":(720*scale),
			"style":" padding-top: 20px;"
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

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function txt2fb(text){
	var fb=$("<a></a>");
	fb.attr("id","txt2fb");
	fb.html(text);
	fb.fancybox().trigger('click');
};

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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
	return text;
};

/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

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
	button.text("glubsch!");
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
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////
// triggered by: 
// arguemnts:	 
// what it does: 
// why: 	 
/////////////////////////////////////////// ACK ALERT //////////////////////////////////////////

function show_old_alert_fb(mid,open_alerts){
	if(open_alerts==0 || is_alarm_open(mid)){
		return;
	};

	// situation where we want this box:
	// 1.) user logs fresh in and there are open_alerts
	// 2.) user was logged-in and there was an alert (other fb still open) that was ignored 

	// generate text and a link to the alertview and display it as fancybox
	var nickname=$("#"+mid+"_name").text();
	var msg="Your safety is the top priority of glubsch! <br><br>";
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
			///
			console.log("test");
			if($("#"+mid+"_old_alerts").length){
				console.log("old_alerts is open");
			};
			///

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


// TODO
// 1. append new alert to open alert_view
// 2. 
