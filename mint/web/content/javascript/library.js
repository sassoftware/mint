// Globals - top level stuff
var cookStatus;
var cookStatusRefreshTime = 2000; /* 2 seconds */
var cookStatusId;
var buildStatus;
var buildStatusRefreshTime = 5000; /* 5 seconds */
var buildStatusId;
var jobsListRefreshTime = 10000; /* 10 seconds */
var jobsListId;
var jobsList = "";
var archDict = "";
var oldBuildStatus = STATUS_UNKNOWN;
var userCache = {};
var groupTroveCache = {};
var buildCache = {};

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

function toggle_element_by_checkbox(elId, checkId) {
    el = $(elId);
    check = $(checkId);

    logDebug("checked: ", check.checked);
    if(check.checked) {
        showElement(elId);
    } else {
        hideElement(elId);
    }
}

// appends a new item to a select element
function appendToSelect(select, value, content, title, className) {
    var o = document.createElement("option");
    o.value = value;
    o.className = className;
    if (title != '') {
        o.title = (title);
    }
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

// get build image type
getBuildTypeDesc = function(aTypeId) {
    return buildTypeNamesShort[aTypeId];
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
    else if (aRow['buildId']) {
        var buildObj = getBuildById(aRow['buildId']);
        if (buildObj) {
            jobDesc = "Build: " + buildObj['name'];
            if (buildObj.buildType) {
                jobDesc += " (" + getBuildTypeDesc(buildObj.buildType) + ")";
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

    if (aRow['status'] == STATUS_RUNNING) {
        var button = BUTTON({'class':'killbutton'}, 'Kill');
        connect(button, 'onclick', function(){killJob(aRow['jobId']);});
        return [ aRow['jobId'], username, humanReadableDate(dateOfInterest),
                jobDesc, aRow['statusMessage'], aRow['hostname'], button ];
    }
    else {
        return [ aRow['jobId'], username, humanReadableDate(dateOfInterest),
                jobDesc, aRow['statusMessage'], aRow['hostname'] ];
    }
};

function killJob(jobId) {
    logDebug('Killing job ' + repr(jobId));
    var req = new JsonRpcRequest("jsonrpc/", "killJob");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(callbackVoid);
    req.send(false, [jobId]);
}


function displayCheckList(fieldname, allItems, selectedItems) {
    var anchorFieldname = 'chklist_'+fieldname;
    
    replaceChildNodes(anchorFieldname, P(null));
    if (allItems.length > 0) {
        for (var i in allItems) {
            var idname = anchorFieldname + '_' + i;
            var attrs = {'id': idname, 'class': 'check indented groupcheck', 'type': 'checkbox', 'name': fieldname, 'value': allItems[i]};
            if (selectedItems) {
                if (selectedItems.indexOf(allItems[i]) >= 0) {
                    attrs['checked'] = 'checked';
                }
            }
            appendChildNodes(anchorFieldname, INPUT(attrs, null),
                    LABEL({'for': idname}, allItems[i]), BR(null));
        }
        appendChildNodes(anchorFieldname, P(null));
        return true;
    }
    else {
        return false;
    }
}

function getGroups(projId, selectedGroups) {
    var processShowGroups = function (aReq) {
        logDebug(aReq.responseText);
        troveList = evalJSONRequest(aReq);
        displayCheckList('groups', troveList, selectedGroups);
    }
    replaceChildNodes('chklist_groups');
    if (projId < 0) {
        return;
    }
    appendChildNodes('chklist_groups', P({'class': 'indented'}, IMG({'src': staticPath + 'apps/mint/images/circle-ball-dark-antialiased.gif'}), "Retrieving groups..."));
    var req = new JsonRpcRequest("jsonrpc/", "getGroupTroves");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processShowGroups);
    req.send(true, [parseInt(projId)]);
}

function callbackVoid() {}
    
// RPC callbacks ------------------------------------------------------------


function processGetCookStatus(aReq) {

    logDebug("[JSON] response: ", aReq.responseText);
    cookStatus = evalJSONRequest(aReq);
    updateStatusArea(cookStatus);


}

function updateStatusArea(jobStatus) {

    var statusAreaEl = $("statusArea");
    var statusMessageEl = $("statusMessage");
    var newStatusMessageEl = DIV({ 'id': 'statusMessage' }, null);

    logDebug(jobStatus);

    if(!jobStatus) {
        var status = STATUS_NOJOB;
    } else {
        var status = jobStatus.status;
        if(status == STATUS_RUNNING)
            setElementClass(statusAreaEl, "running");
        if(status == STATUS_FINISHED)
            setElementClass(statusAreaEl, "finished");
        if(status == STATUS_ERROR)
            setElementClass(statusAreaEl, "error");

        if (status > STATUS_RUNNING) {
            hideElement('statusSpinner');
        } else {
            showElement('statusSpinner');
        }
        replaceChildNodes(newStatusMessageEl, jobStatus.message);
    }
    swapDOM(statusMessageEl, newStatusMessageEl);

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
            finishedJobsList.length + " finished within the last 24 hours)"));

        var tableBody = TBODY(null, null);

        if (queuedJobsList.length > 0) {
            appendChildNodes(tableBody,
                TR(null, TH({ 'colspan': '5', 'colSpan': '5', 'class': 'tablesubhead' },
                    "Queued jobs")),
                    headerRowDisplay(["Job ID", "Submitter", "Time Submitted",
                    "Description", "Last Status Message Received", "Job Server IP"]),
                    map(rowDisplay, queuedJobsList));
        }
        if (runningJobsList.length > 0) {
            appendChildNodes(tableBody,
                TR(null, TH({ 'colspan': '5', 'colSpan': '5', 'class': 'tablesubhead' },
                    "Running jobs")),
                    headerRowDisplay(["Job ID", "Submitter", "Time Started",
                    "Description", "Last Status Message Received", "Job Server IP", "Kill Job"]),
                    map(rowDisplay, runningJobsList));
        }
        if (finishedJobsList.length > 0) {
            appendChildNodes(tableBody,
                TR(null, TH({ 'colspan': '5', 'colSpan': '5', 'class': 'tablesubhead' },
                    "Jobs finished within the last 24 hours")),
                    headerRowDisplay(["Job ID", "Submitter", "Time Finished",
                        "Description", "Last Status Message Received", "Job Server IP"]),
                    map(rowDisplay, finishedJobsList));
        }

        appendChildNodes(jobTable, TABLE({ 'class': 'results' }, tableBody));
    }

    // Disconnect signals to any kill buttons to prevent a memory leak after
    // page refreshes
    var buttons = getElementsByTagAndClassName('button', 'killbutton');
    for (var i in buttons) {
        disconnectAll(buttons[i]);
    }
    // display it
    swapDOM(oldJobTable, jobTable);
}

// RPC calls ----------------------------------------------------------------

function getBuildStatus(buildId, hasFiles) {
    var req = new JsonRpcRequest("jsonrpc/", "getBuildStatus");
    req.setAuth(getCookieValue("pysid"));

    var processGetBuildStatus = function(aReq) {
        logDebug("[JSON] response: ", aReq.responseText);
        buildStatus = evalJSONRequest(aReq);
        if(buildStatus.status == STATUS_NOJOB && hasFiles) {
            buildStatus.status = STATUS_FINISHED;
        }

        updateStatusArea(buildStatus);

        if (buildStatus != null) {
            if (oldBuildStatus == STATUS_UNKNOWN) {
                oldBuildStatus = buildStatus.status;
            }
            if (buildStatus.status < STATUS_FINISHED) {
                callLater(buildStatusRefreshTime / 1000, partial(getBuildStatus, buildId, hasFiles));
            } else {
                logDebug("oldBuildStatus: " + oldBuildStatus);
                if (oldBuildStatus < STATUS_FINISHED) {
                    reloadCallback();
                }
            }
            oldBuildStatus = buildStatus.status;
        }
    }
    req.setCallback(processGetBuildStatus);
    req.send(true, [buildId]);
}

function getCookStatus(jobId) {
    var req = new JsonRpcRequest("jsonrpc/", "getJobStatus");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processGetCookStatus);
    req.send(false, [jobId]);
    // continue calling self until we are finished
    if (cookStatus != null && cookStatus.status < STATUS_FINISHED) {
        cookStatusId = setTimeout("getCookStatus('"+jobId+"')", cookStatusRefreshTime);
    }
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

function deleteBuild(buildId) {
    var req = new JsonRpcRequest("jsonrpc/", "deleteBuild");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [buildId]);
}

function setBuildPublished(buildId) {
    var req = new JsonRpcRequest("jsonrpc/", "setBuildPublished");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [buildId, true]);
}

function startImageJob(buildId) {
    var req = new JsonRpcRequest("jsonrpc/", "startImageJob");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [buildId]);
}

function setMirrorOrder(table, id, order) {
    var req = new JsonRpcRequest("jsonrpc/", "set" + table + "Order");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(reloadCallback);
    req.send(true, [id, order]);
}

// event handlers -----------------------------------------------------------

function setDisabledByElem(elem, disable) {
    for (var i=0; i< elem.childNodes.length; i++) {
        var e = elem.childNodes[i];
        if (e.nodeType == 1) {
            e.disabled = disable;
            setDisabledByElem(e, disable);
        }
    }
    elem.disabled = disable;
}

function onBuildTypeChange(img) {
    // beware of these boundary conditions, when we add more build targets...
    for (t = 1; t <= maxBuildType; t++) {
        var targImg = "formgroup_" + t;
        // ensure we only tinker with elements that exist on the page
        if (document.getElementById(targImg)) {
            var elem = document.getElementById(targImg);
            if (targImg == img) {
                elem.style.display = "";
                setDisabledByElem(elem, false);
                picker.filterFlavors(t);
            }
            else {
                elem.style.display = "none";
                setDisabledByElem(elem, true);
            }
        }
    }
}

// cache-y goodness

function getBuildById(aId) {
    var buildObj;

    lclBuildCallback = function(aReq) {
        logDebug("[JSON] response: ", aReq.responseText);
        buildCache[aId] = evalJSONRequest(aReq);
    };

    if (!buildCache[aId]) {
        var req = new JsonRpcRequest('jsonrpc/', 'getBuild');
        req.setAuth(getCookieValue("pysid"));
        req.setCallback(lclBuildCallback);
        req.send(false, [aId]);
    }

    return buildCache[aId];

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

function getProjectLabels(projectId, selectedProjectLabels) {

    projLabelsCallback = function(aReq) {
        var labels = evalJSONRequest(aReq);
        displayCheckList('labelList', labels, selectedProjectLabels);
    }

    replaceChildNodes('chklist_labelList');
    if (projectId < 0) {
        return;
    }
    appendChildNodes('chklist_labelList', P({'class': 'indented'}, IMG({'src': staticPath + 'apps/mint/images/circle-ball-dark-antialiased.gif'}), "Retrieving labels..."));
    var req = new JsonRpcRequest('jsonrpc/', 'getAllProjectLabels');
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(projLabelsCallback);
    req.send(true, [parseInt(projectId)]);
}

function addOutboundMirror_onProjectChange (e) {
    getProjectLabels(e.src().value);
    getGroups(e.src().value);
    if (e.src().value > 0) {
        $('submitButton').disabled = false;
    } else {
        $('submitButton').disabled = true;
    }
}

// Front Page
function buildIt() {
    newRight = DIV({'id':'activeRight'}, 
                   DIV({'id':'orangeTitle'}, 'Build It.'),
                   'Make your own software appliance in three easy steps.');
    newLeft = DIV({'id':'inactiveLeft'}, 
                  DIV({'id':'inactiveOrangeTitle'}, 'Use It.'),
                  'Check out the software appliances others have built.');
    swapDOM('activeLeft', newLeft);
    swapDOM('inactiveRight', newRight);
    connect('inactiveLeft', 'onclick', useIt);
    connect('inactiveLeft', 'onmouseover', underlineTitle);
    connect('inactiveLeft', 'onmouseout', normalTitle);
    hideElement('applianceLogos');
    updateNodeAttributes('steps', {'style':{'visibility':'visible'}});
    showElement('steps');
}

function useIt() {
    newRight = DIV({'id':'inactiveRight'}, 
                   DIV({'id':'inactiveOrangeTitle'}, 'Build It.'),
                   'Make your own software appliance in three easy steps.');
    newLeft = DIV({'id':'activeLeft'}, 
                  DIV({'id':'orangeTitle'}, 'Use It.'),
                  'Check out the software appliances others have built.');
    swapDOM('inactiveLeft', newLeft);
    swapDOM('activeRight', newRight);
    connect('inactiveRight', 'onclick', buildIt);
    connect('inactiveRight', 'onmouseover', underlineTitle);
    connect('inactiveRight', 'onmouseout', normalTitle);
    showElement('applianceLogos');
    hideElement('steps');
}

function underlineTitle() {
    updateNodeAttributes('inactiveOrangeTitle', 
                         {'style':{'textDecoration':'underline'}});
}

function normalTitle() {
    updateNodeAttributes('inactiveOrangeTitle', 
                         {'style':{'textDecoration':'none'}});
}

//Edit Release
function buttonStatus() {
    var name = getElement('relname');
    if (name.value == '') {
        var button = getElement('submitButton');
        button.disabled = true;
        //Safari mishandles disabled buttons
	updateNodeAttributes(button, {'class':'d'});
        return;
    }
    var version = getElement('relver');
    if (version.value == '') {
        var button = getElement('submitButton');
        //Safari mishandles disabled buttons
	updateNodeAttributes(button, {'class':'d'});
        button.disabled = true;
        return;
    }
    var boxes = getElementsByTagAndClassName('input', 'relCheck');
    var builds = false;
    for (var x = 0; x < boxes.length ; x++) {
        if (boxes[x].checked) {
            builds = true;
            break;
        }
    }
    if (builds) {
        var button = getElement('submitButton');
        button.disabled = false;
        //Safari mishandles disabled buttons
	updateNodeAttributes(button, {'class':''});
    }
    else {
        var button = getElement('submitButton');
        button.disabled = true;
        //Safari mishandles disabled buttons
	updateNodeAttributes(button, {'class':'d'});
    }
}
