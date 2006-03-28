// Globals - top level stuff
var refreshed = false;
var oldStatus = -1;
var cookStatusRefreshTime = 2000; /* 2 seconds */
var cookStatusId;
var releaseStatusRefreshTime = 5000; /* 5 seconds */
var releaseStatusId;
var jobsListRefreshTime = 10000; /* 10 seconds */
var jobsListId;
var jobsList = "global";
var archDict = "global";
var cookStatus = "global";
var releaseStatus = "global";
var oldStatus = STATUS_UNKNOWN;
var userCache = {};
var groupTroveCache = {};
var releaseCache = {};

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

// given a python time (e.g. from time.time()), turns it into a
// human readable string
function humanReadableDate(aPythonicTimestamp) {
    var retval;

    if (!typeof(aPythonicTimestamp) == "number")
        return "Invalid Timestamp";

    var d = (aPythonicTimestamp*1000).toFixed(0);
    if (d > 0) {
        var dObj = new Date();
        dObj.setTime(d);
        retval =  dObj.toLocaleString();
    } else {
        retval = "-";
    }

    return retval;
}


// crude algorithm to make a string plural given a count and a word
// i.e. pluralize(1, "cat") ==> "1 cat", and pluralize(2, "dog") ==> "2 dogs"
// FIXME: doesn't handle exceptions in English (e.g. "mouse", "deer", etc.)
function pluralize(aNumber, aString) {
    if (aNumber != 1) {
        if (aString.slice(-1) == "s"  || aString.slice(-1) == "x" ||
            aString.slice(-2) == "ch" || aString.slice(-2) == "sh") {
            aString += "es";
        } else {
            aString += "s";
        }
    }
    return aNumber + " " + aString;
}

// Normalize a web path by prepending a / if missing, and appending
// a / if missing
function normPath(path) {
    if(path == "")
        path = "/";
    else if(path[path.length-1] != "/")
        path += "/";

    if(path[0] != "/")
        path = "/" + path;

    path = path.replace("//", "/");
    return path;
}

// get release image type
getReleaseImageTypeDesc = function(aTypeId) {
    return releaseImageTypeNamesShort[aTypeId];
};

// function that generates a generic header table row
headerRowDisplay = function(aRow) {
    return TR(null, map(partial(TH, null), aRow));
};

// function that generates a generic table row
rowDisplay = function(aRow) {
    return TR(null, map(partial(TD, null), aRow));
};

// generate a row for the job table
makeJobRowData = function(aRow) {
    var username;
    var jobDesc;
    var dateOfInterest;

    // Get the user ID
    var userObj = getUserById(aRow['userId']);
    if (userObj) {
        username = userObj['username'];
    } else {
        username = "-unknown-";
    }

    // Create a meaningful job description
    if (aRow['groupTroveId']) {
        var groupTroveObj = getGroupTroveById(aRow['groupTroveId']);
        if (groupTroveObj) {
            jobDesc = "Group cook: " + groupTroveObj['recipeName'];
        }
    }
    else if (aRow['releaseId']) {
        var releaseObj = getReleaseById(aRow['releaseId']);
        if (releaseObj) {
            jobDesc = "Release build: " + releaseObj['name'];
            if (releaseObj.imageTypes) {
                jobDesc += " (" + map(getReleaseImageTypeDesc, releaseObj.imageTypes).join(", ") + ")";
            }
        }
    }
    else
    {
        jobDesc = "-Unknown-";
    }

    // pick the appropriate time we are interested in
    // if we are queued, display the submitted time
    // if we are running, display the started time
    // if we are finished, display the finished time
    if (aRow['status'] < STATUS_RUNNING) {
        dateOfInterest = aRow['timeSubmitted'];
    } else if (aRow['status'] == STATUS_RUNNING) {
        dateOfInterest = aRow['timeStarted'];
    } else if (aRow['status'] > STATUS_RUNNING) {
        dateOfInterest = aRow['timeFinished'];
    }

    return [ aRow['jobId'], username, humanReadableDate(dateOfInterest),
                jobDesc, aRow['statusMessage'] ];
};

// RPC callbacks ------------------------------------------------------------
function processGetReleaseStatus(aReq) {
    var oldReleaseStatus = $("releaseStatus");

    logDebug("[JSON] response: ", aReq.responseText);
    releaseStatus = evalJSONRequest(aReq);

    releaseStatusEl = DIV({ 'id': 'releaseStatus', 'class': 'running' }, null);
    if (!releaseStatus) {
        status = STATUS_NOJOB;
    } else {
        status = releaseStatus.status;
        // FIXME: replace this with a status -> class name map or something
        if(status == STATUS_RUNNING)
            setElementClass(releaseStatusEl, "running");
        if(status == STATUS_FINISHED)
            setElementClass(releaseStatusEl, "finished");
        if(status == STATUS_ERROR)
            setElementClass(releaseStatusEl, "error");

        // refresh page when job successfully completes
        // to get new download list
        if ((oldStatus <= STATUS_RUNNING) &&
            (status == STATUS_FINISHED)) {
            window.location.reload();
        }

        // handle edit options; also, spin baton if we're still
        // running
        if (status > STATUS_RUNNING) {
            hideElement('spinner');
            hideElement('editOptionsDisabled');
            showElement('editOptions');
        } else {
            showElement('spinner');
            showElement('editOptionsDisabled');
            hideElement('editOptions');
        }
        replaceChildNodes(releaseStatusEl, SPAN({'style': 'font-weight: bold;'}, "Status: "), SPAN(null, releaseStatus.message));
        oldStatus = status;
    }
    swapDOM(oldReleaseStatus, releaseStatusEl);
}

function processGetCookStatus(aReq) {
    var oldEl = $("releaseStatus");
    var el = DIV({ 'id': 'releaseStatus', 'class': 'running' }, null);

    logDebug("[JSON] response: ", aReq.responseText);
    cookStatus = evalJSONRequest(aReq);

    if(!cookStatus) {
        status = STATUS_NOJOB;
    } else {
        status = cookStatus.status;
        if(status == STATUS_RUNNING)
            setElementClass(el, "running");
        if(status == STATUS_FINISHED)
            setElementClass(el, "finished");
        if(status == STATUS_ERROR)
            setElementClass(el, "error");

        if (status > STATUS_RUNNING) {
            hideElement('spinner');
        } else {
            showElement('spinner');
        }
        replaceChildNodes(el, SPAN({'style': 'font-weight: bold;'}, "Status: "), SPAN(null, cookStatus.message));
    }
    swapDOM(oldEl, el);
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
    hideElement("nameSpinner");
    hideElement("archSpinner");
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
    hideElement("nameSpinner");
    hideElement("archSpinner");
}

function processListActiveJobs(aReq) {
    var jobTable;
    var oldJobTable = $("jobsTable");

    logDebug("[JSON] response: ", aReq.responseText);
    jobsList = evalJSONRequest(aReq);

    // segregate jobsList into mini-lists
    var queuedJobsList = map(makeJobRowData, filter(
        function (job) {
            return (job.status < STATUS_RUNNING);
        }, jobsList));

    var runningJobsList = map(makeJobRowData, filter(
        function (job) {
            return (job.status == STATUS_RUNNING);
        }, jobsList));

    var finishedJobsList = map(makeJobRowData, filter(
        function (job) {
            return (job.status > STATUS_RUNNING);
        }, jobsList));

    // build the jobs display
    jobTable = DIV({ 'id': 'jobsTable' });
    if (jobsList.length == 0) {
        appendChildNodes(jobTable, P(null, "No active jobs."));
    } else {
        appendChildNodes(jobTable, P(null, pluralize(jobsList.length, "job") +
            " (" +
            queuedJobsList.length + " queued, " +
            runningJobsList.length + " running, " +
            finishedJobsList.length + " finished)"));

        var tableBody = TBODY(null, null);

        if (queuedJobsList.length > 0) {
            appendChildNodes(tableBody,
                TR(null, TH({ 'colspan': '5', 'class': 'tablesubhead' },
                    "Queued jobs")),
                    headerRowDisplay(["Job ID", "Submitter", "Time Submitted",
                    "Description", "Last Status Message Received"]),
                    map(rowDisplay, queuedJobsList));
        }
        if (runningJobsList.length > 0) {
            appendChildNodes(tableBody,
                TR(null, TH({ 'colspan': '5', 'class': 'tablesubhead' },
                    "Running jobs")),
                    headerRowDisplay(["Job ID", "Submitter", "Time Started",
                    "Description", "Last Status Message Received"]),
                    map(rowDisplay, runningJobsList));
        }
        if (finishedJobsList.length > 0) {
            appendChildNodes(tableBody,
                TR(null, TH({ 'colspan': '5', 'class': 'tablesubhead' },
                    "Jobs finished within the last 24 hours")),
                    headerRowDisplay(["Job ID", "Submitter", "Time Finished",
                        "Description", "Last Status Message Received"]),
                    map(rowDisplay, finishedJobsList));
        }

        appendChildNodes(jobTable, TABLE({ 'class': 'results' }, tableBody));
    }

    // display it
    swapDOM(oldJobTable, jobTable);
}

// RPC calls ----------------------------------------------------------------

function getReleaseStatus(releaseId) {
    var req = new JsonRpcRequest("jsonrpc/", "getReleaseStatus");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetReleaseStatus);
    req.send(false, [releaseId]);
    if (releaseStatus != null && releaseStatus.status < STATUS_FINISHED) {
        releaseStatusId = setTimeout("getReleaseStatus("+releaseId+")", releaseStatusRefreshTime);
    }
}

function getCookStatus(jobId) {
    var req = new JsonRpcRequest("jsonrpc/", "getJobStatus");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetCookStatus);
    req.send(false, [jobId]);
    // continue calling self until we're finished
    if (cookStatus != null && cookStatus.status < STATUS_FINISHED) {
        cookStatusId = setTimeout("getCookStatus("+jobId+")", cookStatusRefreshTime);
    }
}

function getTroveList(projectId) {
    showElement("nameSpinner");
    hideElement("archSpinner");
    var req = new JsonRpcRequest("jsonrpc/", "getGroupTroves");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetTroveList);
    req.send(true, [projectId]);
}

function getTroveVersionsByArch(projectId, troveNameWithLabel) {
    hideElement("nameSpinner");
    showElement("archSpinner");
    var req = new JsonRpcRequest("jsonrpc/", "getTroveVersionsByArch");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetTroveVersionsByArch);
    req.send(true, [projectId, troveNameWithLabel]);
}

function listActiveJobs(wantOnlyActive) {
    var req = new JsonRpcRequest("jsonrpc/", "listActiveJobs");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processListActiveJobs);
    req.send(false, [wantOnlyActive]);
    // continue calling self until we're finished
    if (jobsList != null) {
        jobsListId = setTimeout("listActiveJobs("+wantOnlyActive+")", jobsListRefreshTime);
    }

}

function reloadCallback() {
    window.location.replace(document.URL);
    // Needed for Safari to reload properly.  Weird.
    setTimeout('window.location.reload()', 0);
}

function setUserLevel(userId, projectId, newLevel) {
    var req = new JsonRpcRequest("jsonrpc/", "setUserLevel");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [userId, projectId, newLevel]);
}

function delMember(projectId, userId) {
    var req = new JsonRpcRequest("jsonrpc/", "delMember");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [projectId, userId, true]);
}

function deleteRelease(releaseId) {
    var req = new JsonRpcRequest("jsonrpc/", "deleteRelease");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [releaseId]);
}

function setReleasePublished(releaseId) {
    var req = new JsonRpcRequest("jsonrpc/", "setReleasePublished");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [releaseId, true]);
}

function startImageJob(releaseId) {
    var req = new JsonRpcRequest("jsonrpc/", "startImageJob");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [releaseId]);
}
// baton --------------------------------------------------------------------

var ticks = 0;
var baton = '-\\|/';

function textWithBaton(text) {

    var newText = text;
    newText += "  " + baton.charAt(ticks);
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

// cache-y goodness

function getReleaseById(aId) {
    var releaseObj;

    lclReleaseCallback = function(aReq) {
        logDebug("[JSON] response: ", aReq.responseText);
        releaseCache[aId] = evalJSONRequest(aReq);
    };

    if (!releaseCache[aId]) {
        var req = new JsonRpcRequest('jsonrpc/', 'getRelease');
        req.setAuth(getCookieValue("pysid"));
        req.setCallback(lclReleaseCallback);
        req.send(false, [aId]);
    }

    return releaseCache[aId];

}

function getUserById(aId) {

    lclUserCallback = function(aReq) {
        logDebug("[JSON] response: ", aReq.responseText);
        userCache[aId] = evalJSONRequest(aReq);
    };

    if (!userCache[aId]) {
        var req = new JsonRpcRequest('jsonrpc/', 'getUserPublic');
        req.setAuth(getCookieValue("pysid"));
        req.setCallback(lclUserCallback);
        req.send(false, [aId]);
    }

    return userCache[aId];

}

function getGroupTroveById(aId) {

    lclGroupTroveCallback = function(aReq) {
        logDebug("[JSON] response: ", aReq.responseText);
        groupTroveCache[aId] = evalJSONRequest(aReq);
    };

    if (!groupTroveCache[aId]) {
        var req = new JsonRpcRequest('jsonrpc/', 'getGroupTrove');
        req.setAuth(getCookieValue("pysid"));
        req.setCallback(lclGroupTroveCallback);
        req.send(false, [aId]);
    }

    return groupTroveCache[aId];

}
