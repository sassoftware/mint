// user interface helpers ---------------------------------------------------

// toggles visiblity of a single element based on the element's id
function toggle_display(tid) {
    el = $(tid);
    if(document.getElementById(tid).style.display == "none") {
        document.getElementById(tid).style.display = "";
        img = document.getElementById(tid + "_expander");
        img.src = img.src.replace('expand', 'collapse');
    }
    else {
        document.getElementById(tid).style.display = "none";
        img = document.getElementById(tid + "_expander");
        img.src = img.src.replace('collapse', 'expand');
    }
}

// similar to toggle_display, except does multiple elements based on name
function toggle_display_by_name(elName) {
    var el_ary = document.getElementsByName(elName);
    for (var i=0; i < el_ary.length; i++) {
        if (el_ary[i].style.display == "none") {
            el_ary[i].style.display = "";
        }
        else if (el_ary[i].style.display == "") {
            el_ary[i].style.display = "none";
        }
    }
}

// appends a new item to a select element
function appendToSelect(select, value, content, className) {
    var o = document.createElement("option");
    o.value = value;
    o.className = className;
    o.appendChild(content);
    select.appendChild(o);
}

// clears the contents of a selectelement
function clearSelection(select) {
    while (select.length > 0) {
        select.remove(0);
    }
}

// returns the value of a named cookie
function getCookieValue (cookie) {
    var e= new RegExp(escape(cookie) + "=([^;]+)");
    if(e.test(document.cookie + ";")) {
        e.exec(document.cookie + ";");
        return unescape(RegExp.$1);
    }
    else
        return false;
}

// RPC callbacks ------------------------------------------------------------

var STATUS_WAITING = 0;
var STATUS_RUNNING = 1;
var STATUS_FINISHED = 2;
var STATUS_DELETED = 3;
var STATUS_ERROR = 4;
var STATUS_NOJOB = 5;
var refreshed = false;
var oldStatus = -1;
var tickerRefreshTime        = 200;  /* 1/5 second */
var cookStatusRefreshTime    = 500;  /* 1/2 second */
var releaseStatusRefreshTime = 5000; /* 5 seconds */
var releaseStatusId;


function processGetReleaseStatus(aReq) {
    var xml = aReq.responseXML;
    el = $("jobStatus");
    var status = getElementsByTagAndClassName("int", null, xml)[0].firstChild.data;

    if(status != oldStatus) {
        if(oldStatus != -1) {
            document.location = document.location;
        }
        oldStatus = status;
    }

    if(status > STATUS_RUNNING) {
        hideElement('editOptionsDisabled');
        showElement('editOptions');
        showElement('downloads');
    } else {
        showElement('editOptionsDisabled');
        hideElement('editOptions');
        hideElement('downloads');
    }

    var statusText = getElementsByTagAndClassName("string", null, xml)[0];
    if(!statusText.firstChild) {
        statusText = "No status";
        status = STATUS_NOJOB;
    } else {
        statusText = statusText.firstChild.nodeValue;
    }
    if(status == STATUS_FINISHED)
        clearTimeout(releaseStatusId);

    replaceChildNodes(el, statusText);
}


var tickerId;
var statusId;
var archDict = "global";


function processGetCookStatus(aReq) {
    var xml = aReq.responseXML;
    el = $("jobStatus");
    var status = getElementsByTagAndClassName("int", null, xml)[0].firstChild.data;
    var statusText = getElementsByTagAndClassName("string", null, xml)[0];

    if(!statusText.firstChild) {
        statusText = "Finished";
        status = STATUS_FINISHED;
    } else {
        statusText = statusText.firstChild.nodeValue;
    }
    if(status == STATUS_FINISHED) {
        clearTimeout(tickerId);
        clearTimeout(statusId);
    }
    replaceChildNodes(el, statusText);
}


function processGetTroveList(aReq) {
    var xml = aReq.responseXML;

    sel = document.getElementById("trove");

    clearSelection(sel);
    var response = getElementsByTagAndClassName("struct", null, xml);
    var members = getElementsByTagAndClassName("member", null, response[0]);

    /* make an empty selection, forcing user to pick */
    appendToSelect(sel, "", document.createTextNode("---"), "trove");

    for(var i = 0; i < members.length; i++) {
        var nameNode = members[i].getElementsByTagName("name")[0];
        var label = nameNode.firstChild.nodeValue;

        var troves = members[i].getElementsByTagName("string");
        for(var j = 0; j < troves.length; j++) {
            var troveName = troves[j].firstChild.nodeValue;
            appendToSelect(sel, troveName + "=" + label, document.createTextNode(troveName), "trove");
        }
    }

}

function processGetTroveVersionsByArch(aReq) {
    logDebug("[JSON] response: ", aReq.responseText);
    archDict = evalJSONRequest(aReq);

    // handle archs
    var archs = keys(archDict).sort();
    var archSel = document.getElementById("arch");
    clearSelection(archSel);
    appendToSelect(archSel, "", document.createTextNode("---"), "arch");
    for (var i in archs) {
        var archStr = archs[i];
        appendToSelect(archSel, archStr, document.createTextNode(archStr), "arch");
    }
    archSel.disabled = false;

}

// RPC calls ----------------------------------------------------------------

function getReleaseStatus(releaseId) {
    var req = new XmlRpcRequest("/xmlrpc", "getReleaseStatus");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetReleaseStatus);
    req.send(releaseId);

    releaseStatusId = setTimeout("getReleaseStatus(" + releaseId + ")", releaseStatusRefreshTime);
}

function getCookStatus(jobId) {
    var req = new XmlRpcRequest("/xmlrpc", "getJobStatus");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetCookStatus);
    req.send(jobId);

    statusId = setTimeout("getCookStatus(" + jobId + ")", cookStatusRefreshTime);
    tickerId = setTimeout("ticker()", tickerRefreshTime);
}

function getTroveList(projectId) {
    var req = new XmlRpcRequest("/xmlrpc", "getGroupTroves");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetTroveList);
    req.send(projectId);

    setTimeout("ticker()", tickerRefreshTime);
}

function getTroveVersionsByArch(projectId, troveNameWithLabel) {
    var req = new JsonRpcRequest("/jsonrpc", "getTroveVersionsByArch");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetTroveVersionsByArch);
    req.send(projectId, troveNameWithLabel);

}

// ticker
// XXX: this could be made mo betta; later?

var ticks = 0;
var direction = 1;

function ticker() {
    el = document.getElementById("pleaseWait");

    if(el) {
        if(direction == 1)
        {
            el.text += ".";
            ticks++;

            if(ticks >= 3)
                direction = -1;
        } else {
            el.text = el.text.substring(0, el.text.length-1);
            ticks--;
            if(ticks == 0)
                direction = 1;
        }
        setTimeout("ticker()", tickerRefreshTime);
    }
}

// event handlers -----------------------------------------------------------

// called when a user selects a trove in the new/edit releases page
function onTroveChange(projectId) {
    var sel = document.getElementById("trove");
    var vSel = document.getElementById("version");
    var archSel = document.getElementById("arch");
    var sb = document.getElementById("submitButton");
    var i = sel.selectedIndex;

    // bail out if selector is changed to a non-trove header selection
    if (i < 1) {
        clearSelection(vSel);
        vSel.disabled = true;
        clearSelection(archSel);
        archSel.disabled = true;
        sb.disabled = true;
        return;
    }

    var troveNameWithLabel = sel.options[sel.selectedIndex].value;
    // XXX: cache values?
    getTroveVersionsByArch(projectId, troveNameWithLabel);
}

function onArchChange() {

    var archSel = document.getElementById("arch");
    var vSel = document.getElementById("version");
    var sb = document.getElementById("submitButton");
    var i = archSel.selectedIndex;

    // handle versions
    clearSelection(vSel);
    appendToSelect(vSel, "", document.createTextNode("---"), "version");
    vSel.disabled = true;

    if (i > 0) {
        selectedArch = archSel.value;
        var versionlist = archDict[selectedArch];
        logDebug(versionlist);
        for (var i in versionlist) {
            appendToSelect(vSel, versionlist[i][1] + " " + versionlist[i][2], document.createTextNode(versionlist[i][0]), "version");
        }
        vSel.disabled = false;
    }
    else {
        sb.disabled = true;
    }

}

function onVersionChange() {

    var vSel = document.getElementById("version");
    var sb = document.getElementById("submitButton");
    var i = vSel.selectedIndex;

    if (i > 0) {
       sb.disabled = false;
    }
    else {
       sb.disabled = true;
    }

}
