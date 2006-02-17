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
var STATUS_UNKNOWN = 9999;
var refreshed = false;
var oldStatus = -1;
var cookStatusRefreshTime    = 2000; /* 2 seconds */
var cookStatusId;
var releaseStatusRefreshTime = 5000; /* 5 seconds */
var releaseStatusId;
var archDict = "global";
var cookStatus = "global";
var releaseStatus = "global";
var oldStatus = STATUS_UNKNOWN;

function processGetReleaseStatus(aReq) {
    var el = $("jobStatus");
    var statusText = "";

    logDebug("[JSON] response: ", aReq.responseText);
    releaseStatus = evalJSONRequest(aReq);

    if (!releaseStatus) {
        statusText = "No status";
        status = STATUS_NOJOB;
    } else {

        // refresh page when job successfully completes
        // to get new download list
        if ((oldStatus <= STATUS_RUNNING) &&
            (releaseStatus.status == STATUS_FINISHED)) {
            document.location = document.location;
        }

        // handle edit options; also, spin baton if we're still
        // running
        if (releaseStatus.status > STATUS_RUNNING) {
            hideElement('editOptionsDisabled');
            showElement('editOptions');
            statusText = releaseStatus.message;
        } else {
            showElement('editOptionsDisabled');
            hideElement('editOptions');
            statusText = textWithBaton(releaseStatus.message);
        }

        // show downloads only when finished
        if (releaseStatus.status == STATUS_FINISHED || releaseStatus.status == STATUS_UNKNOWN) {
            showElement('downloads');
        } else {
            hideElement('downloads');
        }

        oldStatus = status;
    }

    replaceChildNodes(el, statusText);
}

function processGetCookStatus(aReq) {
    var el = $("jobStatus");
    var statusText = "";

    logDebug("[JSON] response: ", aReq.responseText);
    cookStatus = evalJSONRequest(aReq);

    if(!cookStatus.message) {
        statusText = "No status";
        status = STATUS_NOJOB;
    } else {
        if (cookStatus.status > STATUS_RUNNING) {
            statusText = cookStatus.message;
        } else {
            statusText = textWithBaton(cookStatus.message);
        }
    }

    replaceChildNodes(el, statusText);

}

function processGetTroveList(aReq) {
    var sel = $("trove");
    logDebug("[JSON] response: ", aReq.responseText);
    var trovelist = evalJSONRequest(aReq);

    /* make an empty selection, forcing user to pick */
    clearSelection(sel);
    appendToSelect(sel, "", document.createTextNode("---"), "trove");

    for (var label in trovelist) {
        var troveNames = sorted(trovelist[label]);
        for (var troveNameIdx in troveNames) {
            var troveName = troveNames[troveNameIdx];
            appendToSelect(sel, troveName + "=" + label, document.createTextNode(troveName), "trove");
        }
    }

}

function processGetTroveVersionsByArch(aReq) {
    logDebug("[JSON] response: ", aReq.responseText);
    archDict = evalJSONRequest(aReq);

    // handle archs
    var archs = keys(archDict).sort();
    var archSel = $("arch");
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
    var req = new JsonRpcRequest("/jsonrpc", "getReleaseStatus");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetReleaseStatus);
    req.send(false, [releaseId]);
    if (releaseStatus != null && releaseStatus.status < STATUS_FINISHED) {
        releaseStatusId = setTimeout("getReleaseStatus("+releaseId+")", releaseStatusRefreshTime);
    }
}

function getCookStatus(jobId) {
    var req = new JsonRpcRequest("/jsonrpc", "getJobStatus");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetCookStatus);
    req.send(false, [jobId]);
    // continue calling self until we're finished
    if (cookStatus != null && cookStatus.status < STATUS_FINISHED) {
        cookStatusId = setTimeout("getCookStatus("+jobId+")", cookStatusRefreshTime);
    }
}

function getTroveList(projectId) {
    var req = new JsonRpcRequest("/jsonrpc", "getGroupTroves");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetTroveList);
    req.send(true, [projectId]);
}

function getTroveVersionsByArch(projectId, troveNameWithLabel) {
    var req = new JsonRpcRequest("/jsonrpc", "getTroveVersionsByArch");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetTroveVersionsByArch);
    req.send(true, [projectId, troveNameWithLabel]);
}

function reloadCallback() {
    window.location.reload();
}

function setUserLevel(userId, projectId, newLevel) {
    var req = new JsonRpcRequest("/jsonrpc", "setUserLevel");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [userId, projectId, newLevel])
}

// baton --------------------------------------------------------------------

var ticks = 0;
var baton = '-\\|/';

function textWithBaton(text) {

    var newText = text;
    newText += "  " + baton[ticks];
    ticks = ((ticks + 1) % baton.length);
    return newText;

}

// NOTE: ticker removed for now until we come up with something better

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

    var archSel = $("arch");
    var vSel = $("version");
    var sb = $("submitButton");
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
        handleReleaseTypes(selectedArch);
    }
    else {
        sb.disabled = true;
    }

}

function onVersionChange() {

    var vSel = $("version");
    var sb = $("submitButton");
    var i = vSel.selectedIndex;

    if (i > 0) {
       sb.disabled = false;
    }
    else {
       sb.disabled = true;
    }

}


/* TODO: This begs for a more configurable way based on supported
         available job server capabilities.  */
function handleReleaseTypes(aSelectedArch) {

    var arch = $('arch');
    var isoImageSel  = $('imagetype_1');
    var qemuImageSel = $('imagetype_7');
    var vmwareImageSel = $('imagetype_8');

    if (aSelectedArch == "x86_64") {
        isoImageSel.disabled = false;
        qemuImageSel.disabled = true;
        vmwareImageSel.disabled = true;
        isoImageSel.click();
    } else {
        isoImageSel.disabled = false;
        qemuImageSel.disabled = false;
        vmwareImageSel.disabled = false;
    }

}
