/*
 Copyright (c) 2005 rPath Inc.
 All rights reserved

On pages that allow for rmake manipulation do the following:
    On page load:
        Find the links (which currently add/delete via URLs) replace with javascript ajax commands
            addrMakeBuildTrove
            deleterMakeBuildTrove
    On link click:
        Post the xmlrpc request to add/delete the trove
        Wait for the return value
        Populate the box with the new data returned from the xmlrpc call

    On rMake build:
        While rMake build is in progress, sleep periodically
        Post an xmlrpc request to update status
        Populate the builder pane of the status boxes with the proper content
*/

var rMakeBuildId = 0;
var statusTimeout = 1000;
var rMakeBuildStatus = 0;
var savedTroveList = [];
var savedrMakeBuild = null;

function getrMakeBuild() {
    var req = new JsonRpcRequest("jsonrpc/", "getrMakeBuild");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processgetrMakeBuild);
    req.send(true, [rMakeBuildId]);
}

function processgetrMakeBuild(aReq) {
    var rMakeBuild = evalJSONRequest(aReq);
    if (savedrMakeBuild == null) {
        savedrMakeBuild = rMakeBuild;
    }
    rMakeBuildStatus = rMakeBuild['status'];
    var rMakeBuildAction = document.getElementById('rMakeBuildNextAction');
    var rMakeBuilderStatus = document.getElementById('rmakebuilder-status');
    listrMakeBuildTroves();
    var stop = 0;
    if ((rMakeBuild['statusMessage'] != savedrMakeBuild['statusMessage']) | (rMakeBuild['status'] != savedrMakeBuild['status'])) {
        var statusClass = 'statusRunning';
        for (var statusIndex in jobStatusCodes) {
            if (statusIndex == rMakeBuildStatus) {
               statusClass = jobStatusCodes[statusIndex];
            }
        }
        if (rMakeBuilderStatus != null) {
            swapDOM(rMakeBuilderStatus, DIV({id : 'rmakebuilder-status', class : statusClass}, rMakeBuild['statusMessage']));
        }
    }
    for (var stopIndex in stopStatusList) {
        if (rMakeBuildStatus == stopStatusList[stopIndex]) {
            stop = 1;
        }
    }
    if (rMakeBuildAction != null) {
        if (rMakeBuildStatus == 99) {
            swapDOM(rMakeBuildAction, A({id: 'rMakeBuildNextAction', class : 'option', style : 'display: inline;', href : BaseUrl + 'commandrMake?command=commit'}, 'Commit'));
        }
        if (rMakeBuildStatus == -1) {
            swapDOM(rMakeBuildAction, A({id: 'rMakeBuildNextAction', class : 'option', style : 'display: inline;', href : BaseUrl + 'resetrMakeStatus'}, 'Reset'));
        }
    }
    if (!stop) {
        setTimeout("getrMakeBuild()", statusTimeout);
    }
    savedrMakeBuild = rMakeBuild;
}

function listrMakeBuildTroves() {
    var req = new JsonRpcRequest("jsonrpc/", "listrMakeBuildTroves");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processListrMakeBuildTroves);
    req.send(true, [rMakeBuildId]);
}

function processListrMakeBuildTroves(aReq) {
    var troveList = evalJSONRequest(aReq);
    if (savedTroveList.length == 0) {
        savedTroveList = troveList;
    }
    for (var trvIndex in troveList) {
        var trvDict = troveList[trvIndex];
        var itemId = trvDict['rMakeBuildItemId'];
        var trvStatus = trvDict['status'];
        if (trvStatus != savedTroveList[trvIndex]['status']) {
            var statusIcon = document.getElementById("rmakebuilder-statusicon-" + itemId);
            if(statusIcon != null) {
                swapDOM(statusIcon, IMG({src: statusIcons[trvStatus], id : 'rmakebuilder-statusicon-' + itemId}));
            }
        }
        if ((trvDict['statusMessage'] != savedTroveList[trvIndex]['statusMessage']) | (trvStatus != savedTroveList[trvIndex]['status'])) {
            var statusBox = document.getElementById("rmakebuilder-item-status-" + itemId);
            if(statusBox != null) {
                var classCode = 'statusRunning';
                for (var statusIndex in trvStatusCodes) {
                    if (statusIndex == trvStatus) {
                        classCode = trvStatusCodes[statusIndex];
                    }
                }
                swapDOM(statusBox, TD({id: "rmakebuilder-item-status-" + itemId, "class" : classCode, width : "100%"}, trvDict['statusMessage']));
            }
        }
    }
    savedTroveList = troveList;
}

function initrMakeManager(newrMakeBuildId) {
    rMakeBuildId = newrMakeBuildId;
    getrMakeBuild();
}
