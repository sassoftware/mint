// BROWSER DETECTION
var isIE = false;
var isIE4 = false;
var isNN4 = false;
var isNNold = false;
var isNN = false;
var isOpera = false;
var hasLayers = false;

DetectBrowser();
function DetectBrowser() {
	var ua = navigator.userAgent.toLowerCase();
	var ps = navigator.productSub;
	
	if (ua.indexOf("opera") > -1) { isOpera = true; }
	if (document.all && !isOpera) { isIE = parseFloat(ua.substring(ua.indexOf("msie")+5,ua.length)); }
	if (parseInt(isIE) == 4) { isIE4 = true; }
	if ((navigator.appName.toLowerCase()=="netscape") && !document.getElementById) { isNN4 = true; }
	if (isNN4 || (document.getElementById && !document.all)) { isNN = true; }
	if (isNN4 || (ps < 20020823)) { isNNold = true; }
	
	if (isNN || isIE || (isOpera >= 7)) { hasLayers = true; }
}

var PX = (navigator.productSub)?"px":""; //units attached to style properties for positioning




// GENERAL LAYER FUNCTIONS
function get_obj_style(id) {
	if (get_obj(id)) {
		if (isNN4) { return get_obj(id); }
		else { return get_obj(id).style; }
	}
}

function get_obj(id) {
	if (isNN4) { return document.layers[id]; }
	else if (isIE4) { return document.all[id]; }
	else { return document.getElementById(id); }
}

function get_obj_pos(id) {
	var x;
	var y;
	if (get_obj(id)) {
		if (isIE4) {
			x = parseInt(get_obj_style(id).pixelLeft);
			y = parseInt(get_obj_style(id).pixelTop);
		}
		else {
			x = parseInt(get_obj(id).offsetLeft);
			y = parseInt(get_obj(id).offsetTop);
		}
	}
	return [x,y];
}

function set_obj_pos(id,x,y) {
	if (get_obj(id)) {
		if (isIE4) {
			get_obj_style(id).pixelLeft = x + PX;
			get_obj_style(id).pixelTop = y + PX;
		}
		else {
			get_obj_style(id).left = x + PX;
			get_obj_style(id).top = y + PX;
		}
	}
}

function get_obj_dim(id) {
	var x;
	var y;
	if (get_obj(id)) {
		if (isNN4) {
			x = parseInt(get_obj(id).clip.width);
			y = parseInt(get_obj(id).clip.height);
		}
		else {
			x = parseInt(get_obj(id).offsetWidth);
			y = parseInt(get_obj(id).offsetHeight);
		}
	}
	return [x,y];
}

var d_r=(isIE&&document.compatMode=="CSS1Compat")? "document.documentElement":"document.body"
function get_win_dim() {
	return [parseInt(isNNold?window.innerWidth:eval(d_r).clientWidth),parseInt(isNNold?window.innerHeight:eval(d_r).clientHeight)];
}

function show_obj(id,flag) {
	if (get_obj(id)) {
		if ( flag == 1 ) {	
			if (isNN4) { get_obj_style(id).visibility = "show"; }
			else { get_obj_style(id).visibility = "visible"; }
		}
		else {
			if (isNN4) { get_obj_style(id).visibility = "hide"; }
			else { get_obj_style(id).visibility = "hidden"; }
		}
	}
}




// POPUP SPECIFIC FUNCTIONS
var current_popup = 0;

function show_popup(lnk,id) {
	var lnk_pos = get_obj_pos(lnk);
	var lnk_dim = get_obj_dim(lnk);
	
	new_pos_x = lnk_pos[0];
	new_pos_y = lnk_pos[1] + lnk_dim[1];
	
	set_obj_pos(id,new_pos_x,new_pos_y);
	show_obj(id,1);
	current_popup = id;
}

function hide_popup(id, refresh) {
	show_obj(id,0);
	set_obj_pos(id,0,-800);
	current_popup = 0;
}

function handle_window_resize() {
	if (current_popup != 0) {
		if (isNN4) { location.reload(); }
		else { hide_popup(current_popup); }
	}
}

if (hasLayers) { window.onresize = handle_window_resize; }
