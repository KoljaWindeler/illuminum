<?php
///////////////// server status ///////////////////////////
$body='<h1 id="l10n_title">Python WebSocket-Server<br>Status: ';
unset($output);
exec('ps -ax|grep "python3" | grep "main.py"| grep -v "grep"',$output,$return_var);
if(!empty($output[0])){	// python serer is running add everything
	$body.='<font color="green">online</font>';

	$body.='</h1>';
	$extra_header='<script type="text/javascript" src="jscolor/jscolor.js"></script>
		<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script>
		<script type="text/javascript" src="wsjq.js"></script>';
	// Click here: <input class="color {onImmediateChange:\'updateInfo(this);\'}" value="66ff00">';
	// add ws display stuff
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
    <body>
        <table height="100%" width="100%">
            <tbody><tr>
                <td align="center" valign="middle">';
$footer='</td></tr></tbody></table></body></html>';
///////////////// header ///////////////////////////
echo $header;
echo $body;
echo $footer;
?>

