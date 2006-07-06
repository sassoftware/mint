//
// Copyright (C) 2006 rPath, Inc
// All Rights Reserved
//

var labelsCache = {};
var versionCache = {};

var staticPath = '';

var green = {'style': 'color: green; font-weight: bold;'};
var gray = {'style': 'color: gray;'};

var spinnerImg = 'apps/mint/images/circle-ball-dark-antialiased.gif';
var nextImg = 'apps/mint/images/next.gif';
var prevImg = 'apps/mint/images/prev.gif';
var prevImgDisabled = 'apps/mint/images/prev_disabled.gif';

//
// some DOM helper functions
//
function forwardLink(attrs, text) {
    return LI(null, A(attrs, IMG({'src': staticPath + nextImg}), " " + text));
}

function returnImg() {
    return IMG({'src': staticPath + prevImg});
}

function disabledReturn() {
    return DIV(gray, IMG({'src': staticPath + prevImgDisabled}), " Back");
}

// ctor
function TrovePicker(projectId, serverName, troveName, pickerId, mintStaticPath) {
    this.projectId = projectId;
    this.serverName = serverName;
    this.troveName = troveName;
    this.elId = pickerId;
    staticPath = mintStaticPath;

    logDebug(this.elId);
    this.buildTrovePicker();
}

TrovePicker.prototype.troveName = null;
TrovePicker.prototype.serverName = null;
TrovePicker.prototype.label = null;
TrovePicker.prototype.version = null;
TrovePicker.prototype.flavorCache = null;
TrovePicker.prototype.flavorDict = null;

TrovePicker.prototype.working = function(isWorking) {
    if(isWorking) {
        showElement(this.elId + 'spinnerList');
        hideElement(this.elId + 'selectionList');
    }
    else {
        hideElement(this.elId + 'spinnerList');
        showElement(this.elId + 'selectionList');
    }
}

TrovePicker.prototype.buildTroveSpec = function(name, version, flavor) {
    return DIV({'id': this.elId + 'troveSpec'},
        DIV((name ? green : gray), "Name: ", name),
        DIV((version ? green : gray), "Version: ", version),
        DIV((flavor ? green : gray), "Flavor: ", flavor)
    );
}

// Build the initial DOM for the trove picker and
// begin retrieving all leaves for a given
// trove name on a server.
TrovePicker.prototype.buildTrovePicker = function() {
    oldEl = $(this.elId);
    picker = DIV({'id': this.elId, 'class': 'trovePicker'})
    spinner = UL({'id': this.elId + 'spinnerList'},
        LI(null, "Loading...", IMG({'src': staticPath + spinnerImg}))
    );
    appendChildNodes(picker, SPAN({'id': this.elId + 'prompt', 'class': 'prompt'}),
        P({'style': 'float: right;'},
            SPAN({'id': this.elId + 'next'}, null), 
            " ",
            IMG({'src': staticPath + nextImg})
        ),
        P({'id': 'return'}),
        spinner,
        UL({'id': this.elId + 'selectionList'}),
        this.buildTroveSpec('', '', '')
    );
    swapDOM(oldEl, picker);
    this.getAllTroveLabels();
}

// Show all flavors available for a given trove and version
TrovePicker.prototype.showTroveFlavors = function(e) {
    this.version = e.src().version;

    replaceChildNodes($(this.elId + 'troveSpec'),
        this.buildTroveSpec(this.troveName, this.version, ''));
    oldList = $(this.elId + 'selectionList');
    ul = UL({ 'id': this.elId + 'selectionList' });

    for(var i in this.flavorCache[this.version]) {
        flavor = this.flavorCache[this.version][i];
        appendChildNodes(ul, forwardLink(null, this.flavorDict[flavor]));

        // return to getTroveVersions
        returnLink = A(null, returnImg(), " Back");
        returnLink.label = this.label;
        connect(returnLink, "onclick", this, "getTroveVersions");
        replaceChildNodes($('return'), returnLink);
    }
    swapDOM(oldList, ul);
    this.working(false);
    replaceChildNodes($(this.elId + 'prompt'), "Please choose a flavor:");
}

// Show all versions of a trove on a given label
TrovePicker.prototype.getTroveVersions = function(e) {
    this.label = e.src().label;
    var par = this;
    var key = this.label + "=" + this.troveName;

    var setupList = function(versionList) {
        var versionDict = req[0];
        var versionList = req[1];
        oldList = $(par.elId + 'selectionList');
        ul = UL({ 'id': par.elId + 'selectionList' });

        par.flavorCache = versionDict;
        par.flavorDict = req[2];

        for(var i in versionList) {
            link = forwardLink(null, versionList[i]);
            link.version = versionList[i];
            connect(link, "onclick", par, "showTroveFlavors");
            appendChildNodes(ul, link);
        }
        swapDOM(oldList, ul);
        par.working(false);
        replaceChildNodes($(par.elId + 'prompt'), "Please choose a version:");
        replaceChildNodes($(par.elId + 'next'), "Next: Choose a Version");
        replaceChildNodes($(par.elId + 'troveSpec'),
            par.buildTroveSpec(par.troveName, par.label, ''));

        // return to getAllTroveLabels
        returnLink = A(null, returnImg(), " Back");
        connect(returnLink, "onclick", par, "getAllTroveLabels");
        replaceChildNodes($('return'), returnLink);
    };

    var callback = function(aReq) {
        logDebug("[JSON] response: ", aReq.responseText);

        req = evalJSONRequest(aReq);
        versionCache[key] = req;
        setupList(req);
    };

    if(!versionCache[key]) {
        this.working(true);
        var req = new JsonRpcRequest("jsonrpc/", "getTroveVersions");
        req.setCallback(callback);
        req.send(true, [this.projectId, this.label, this.troveName]);
    } else {
        setupList(versionCache[key]);
    }
}

// Fetch all labels a trove exists on a given server
TrovePicker.prototype.getAllTroveLabels = function() {
    logDebug("top of getAllTroveLabels");
    var key = this.serverName + "=" + this.troveName;
    var par = this; // save the parent for the subfunction's use

    var setupList = function(labelList) {
        oldList = $(par.elId + 'selectionList');
        ul = UL({ 'id': par.elId + 'selectionList' });

        for(var i in labelList) {
            link = forwardLink(null, labelList[i]);
            link.label = labelList[i];
            connect(link, "onclick", par, "getTroveVersions");
            appendChildNodes(ul, link);
        }
        swapDOM(oldList, ul);
        par.working(false);
        replaceChildNodes($(par.elId + 'prompt'), "Please choose a label:");
        replaceChildNodes($(par.elId + 'next'), "Next: Choose a Version");
        replaceChildNodes($(par.elId + 'troveSpec'),
            par.buildTroveSpec(par.troveName, par.serverName, ''));
        replaceChildNodes($('return'), disabledReturn());
    };

    var callback = function(aReq) {
        logDebug("[JSON] response: ", aReq.responseText);

        labelList = evalJSONRequest(aReq);
        labelsCache[key] = labelList;
        setupList(labelList);
    };

    if(!labelsCache[key]) {
        this.working(true);
        var req = new JsonRpcRequest("jsonrpc/", "getAllTroveLabels");
        req.setAuth(getCookieValue("pysid"));
        req.setCallback(callback);
        req.send(true, [this.projectId, this.serverName, this.troveName]);
    } else {
        setupList(labelsCache[key]);
    }
}
