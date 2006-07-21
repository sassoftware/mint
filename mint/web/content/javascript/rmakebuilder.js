/*
 Copyright (c) 2005 rPath Inc.
 All rights reserved

On pages that allow for rmake manipulation do the following:
    On page load:
        Find the links replace with javascript ajax commands
            addrMakeBuildTrove
            deleterMakeBuildTrove
    On link click:
        Post the xmlrpc request to add/delete the trove
        Wait for the return value
        Populate the box with the new data returned from the xmlrpc call
            This includes changing the next action command if appropriate

    On rMake build:
        While rMake build is in progress, sleep periodically
        Post an xmlrpc request to update status
        Populate the builder pane or the status boxes with the proper content
*/

var rMakeBuildId = 0;
var statusTimeout = 1;
var savedTroveList = [];
var savedrMakeBuild = null;
var commitFailed = 0;
var numTroves = 0;

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
        savedrMakeBuild['jobId'] = 0;
    }
    var rMakeBuildAction = document.getElementById('rMakeBuildNextAction');
    var rMakeBuilderStatus = document.getElementById('rmakebuilder-status');
    var rMakeBuilderJobId = document.getElementById('rmakebuilder-jobid');
    if (rMakeBuild['statusMessage'].match('Commit failed.*')) {
        commitFailed = 1;
    }
    listrMakeBuildTroves();
    var stop = 0;
    if (rMakeBuild['jobId'] != savedrMakeBuild['jobId']) {
        if ((rMakeBuilderJobId != null) && (rMakeBuild['jobId'] != 0)) {
            swapDOM(rMakeBuilderJobId, H3({id : "rmakebuilder-jobid"}, "rMake Job ID: " + rMakeBuild['jobId']));
        }
    }
    if ((rMakeBuild['statusMessage'] != savedrMakeBuild['statusMessage']) || (rMakeBuild['status'] != savedrMakeBuild['status']) || (commitFailed)) {
        var statusClass = 'statusRunning';
        for (var statusIndex in jobStatusCodes) {
            if (statusIndex == rMakeBuild['status']) {
                statusClass = jobStatusCodes[statusIndex];
            }
        }
        if (commitFailed) {
            statusClass = jobStatusCodes[buildjob['JOB_STATE_FAILED']];
        }
        if (rMakeBuilderStatus != null) {
            swapDOM(rMakeBuilderStatus, DIV({id : 'rmakebuilder-status', class : statusClass}, rMakeBuild['statusMessage']));
        }
    }
    for (var stopIndex in stopStatusList) {
        if (rMakeBuild['status'] == stopStatusList[stopIndex]) {
            stop = 1;
        }
    }
    if (rMakeBuildAction != null) {
        if (rMakeBuild['status'] == buildjob['JOB_STATE_BUILT']) {
            swapDOM(rMakeBuildAction, A({id: 'rMakeBuildNextAction', class : 'option', style : 'display: inline;', href : BaseUrl + 'commandrMake?command=commit'}, 'Commit'));
        }
        if ((rMakeBuild['status'] == buildjob['JOB_STATE_COMMITTED']) || (rMakeBuild['status'] == buildjob['JOB_STATE_FAILED'])){
            swapDOM(rMakeBuildAction, A({id: 'rMakeBuildNextAction', class : 'option', style : 'display: inline;', href : 'javascript:resetrMakeStatus()'}, 'Reset'));
        }
    }
    if (!stop) {
        callLater(statusTimeout, getrMakeBuild);
        /* setTimeout("getrMakeBuild()", statusTimeout); */
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
    numTroves = troveList.length;
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
        if ((trvDict['statusMessage'] != savedTroveList[trvIndex]['statusMessage']) || (trvStatus != savedTroveList[trvIndex]['status']) || commitFailed) {
            var statusBox = document.getElementById("rmakebuilder-item-status-" + itemId);
            if(statusBox != null) {
                var classCode = 'statusRunning';
                for (var statusIndex in trvStatusCodes) {
                    if (statusIndex == trvStatus) {
                        classCode = trvStatusCodes[statusIndex];
                    }
                }
                if (commitFailed) {
                    classCode = trvStatusCodes[buildtrove['TROVE_STATE_FAILED']];
                }
                swapDOM(statusBox, TD({id: "rmakebuilder-item-status-" + itemId, "class" : classCode, width : "100%"}, trvDict['statusMessage']));
            }
        }
    }
    savedTroveList = troveList;
}

function deleterMakeBuildTrove(troveId) {
    var req = new JsonRpcRequest("jsonrpc/", 'delrMakeBuildTrove');
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(rMakeTroveDeleted);
    req.send(true, [troveId]);
}

function addrMakeBuildTroveByLabel(name, label) {
    var req = new JsonRpcRequest("jsonrpc/", 'addrMakeBuildTrove');
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(rMakeTroveAdded);
    req.send(true, [rMakeBuildId, name, label]);
}

function addrMakeBuildTroveByProject(name, project) {
    var req = new JsonRpcRequest("jsonrpc/", 'addrMakeBuildTroveByProject');
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(rMakeTroveAdded);
    req.send(true, [rMakeBuildId, name, project]);
}

function resetrMakeStatus(troveId) {
    var req = new JsonRpcRequest("jsonrpc/", 'resetrMakeBuildStatus');
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(function() {setTimeout('window.location.reload()', 0);});
    req.send(true, [rMakeBuildId]);
}

function rMakeTroveAdded (aReq) {
    var trvDict = evalJSONRequest(aReq);
    if (trvDict['trvName']) {
        newRow = TR({'id' : 'rmakebuilder-item-' + trvDict['rMakeBuildItemId']},
                    TD({}, ''),
                    TD({}, A({'href' : BaseUrl + 'repos/' + trvDict['shortHost'] + 'troveInfo?t=' + trvDict['trvName']}, trvDict['trvName'])),
                    TD({}, A({'href' : BaseUrl + 'repos/' + trvDict['shortHost'] + '/browse'}, trvDict['shortHost'])),
                    TD({}, A({'href' : 'javascript:deleterMakeBuildTrove(' + trvDict['rMakeBuildItemId'] + ');'},'X')));
        var tableNode = document.getElementById('rmakebuilder-tbody');
        tableNode.appendChild(newRow);
        numTroves = numTroves + 1;
        var rMakeBuildAction = document.getElementById('rMakeBuildNextAction');
        if(rMakeBuildAction) {
            swapDOM(rMakeBuildAction, A({id: 'rMakeBuildNextAction', class : 'option', style : 'display: inline;', href : BaseUrl + 'commandrMake?command=build'}, 'Build'));
        }
    }
}

function rMakeTroveDeleted(aReq) {
    var rMakeBuildItemId = evalJSONRequest(aReq);
    var trvRow = document.getElementById('rmakebuilder-item-' + rMakeBuildItemId);
    if(trvRow) {
        swapDOM('rmakebuilder-item-' + rMakeBuildItemId, null);
        numTroves = numTroves - 1;
        var rMakeBuildAction = document.getElementById('rMakeBuildNextAction');
        if((!numTroves) && rMakeBuildAction) {
            swapDOM(rMakeBuildAction, A({id: 'rMakeBuildNextAction', class : 'option', style : 'display: inline;', href : BaseUrl + 'editrMake?id=' + rMakeBuildId}, 'Edit'));
        }
    }
}

LinkManager.prototype.getUrlData = function(link) {
    var ques = link.indexOf('?');
    var args = new Object();
    var argstr = link.substring(ques+1, link.length);
    arglist = argstr.split(/;|&/);
    for (var i=0; i < arglist.length; i++) {
        var key, value;
        var x = arglist[i].split('=');
        args[x[0]] = x[1];
    }
    return args;
}

function LinkManager() {
    bindMethods(this);
}

LinkManager.prototype.reworkLinks = function () {
    anchors = document.getElementsByTagName("a");
    for(var i=0; i < anchors.length; i++) {
        var anchor = anchors[i];
        var href = anchor.href;
        if (href.indexOf('deleterMakeTrove') >= 0) {
            var args = this.getUrlData(href);
            anchor.href = "javascript:deleterMakeBuildTrove(" + args['troveId'] + ");";
        }
        else if (href.indexOf('addrMakeTrove') >= 0) {
            var args = this.getUrlData(href);
            if (args['label']) {
                anchor.href = "javascript:addrMakeBuildTroveByLabel('" + args['trvName'] + "', '" + args['label'] + "');";
            }
            else if(true || args['projectName']){
                anchor.href = "javascript:addrMakeBuildTroveByProject('" + args['trvName'] + "', '" + args['projectName'] + "');";
            }
        }
    }
}

linkManager = null;

function initrMakeManager(newrMakeBuildId) {
    rMakeBuildId = newrMakeBuildId;
    linkManager = new LinkManager();
    linkManager.reworkLinks();
    getrMakeBuild();
}
