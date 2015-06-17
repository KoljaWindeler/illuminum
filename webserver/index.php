<?php
///////////////// server status ///////////////////////////
$body='<img src="images/logobw.png"><h1 id="l10n_title">Welcome to glubsch</h1>';
unset($output);
exec('ps -ax|grep "python3" | grep "main.py"| grep -v "grep"',$output,$return_var);
if(!empty($output[0])){	// python serer is running add everything
	$extra_header='<script type="text/javascript" src="jscolor/jscolor.js"></script>
		<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script>
		<script type="text/javascript" src="wsjq.js"></script>
		<script src="jquery-ui.js"></script>
		<script src="jquery.ui.touch-punch.min.js"></script>
		<script src="jquery.bxslider.min.js"></script>
		<script src="fancyBox/jquery.fancybox.pack.js"></script>
		<link rel="stylesheet" href="jquery-ui.css"/>
		<link rel="stylesheet" href="fancyBox/jquery.fancybox.css" type="text/css" media="screen" />
		<link rel="stylesheet" href="jquery.bxslider.css"/>';
	// add ws display stuff
	$body.='<br>';
	$body.='<div id="clients"></div>';
}

///////////////// server status ///////////////////////////

///////////////// header ///////////////////////////
$header='<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en"><head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta http-equiv="x-dns-prefetch-control" content="off">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
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

