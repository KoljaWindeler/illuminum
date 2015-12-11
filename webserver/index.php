<?php
if($_GET['useas']=="dummy"){
	    header_remove('X-Frame-Options');
	exit(0);
};
///////////////// server status ///////////////////////////
$v=exec('git -C /home/ubuntu/python/illumino/ rev-list HEAD --count');
$body='<div class="logo_l1">welcome to </div><div class="logo_l2">illuminum</div>';
unset($output);
exec('ps -ax|grep "python3" | grep "main.py"| grep -v "grep"',$output,$return_var);
if(!empty($output[0])){	// python serer is running add everything
	$extra_header='
		<script src="https://maps.googleapis.com/maps/api/js"></script>
		<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script>
		<script src="js/md5.js"></script>
		<script src="js/wsjq.js"></script>
		<script src="js/jquery-ui.js"></script>
		<script src="js/jquery.ui.touch-punch.min.js"></script>
		<script src="js/fancyBox/jquery.fancybox.pack.js"></script>

		<link rel="stylesheet" href="css/jquery-ui.css"/>
		<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
		<link rel="stylesheet" href="js/fancyBox/jquery.fancybox.css" type="text/css" media="screen" />';
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
        <link rel="stylesheet" href="css/design.css" type="text/css" media="screen" charset="utf-8">
        <title>illuminum webapp v.'.$v.'</title>
	'.$extra_header.'
    </head>
    <body>';
 
$footer='</body></html>';

///////////////// header ///////////////////////////
echo $header;
echo $body;
echo $footer;
?>
        
