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
        P({'id': 'return'}),
        spinner,
        UL({'id': this.elId + 'selectionList'}),
        INPUT({'id': this.elId + 'Name', 'name': this.elId + 'Name', 'type': 'hidden'}),
        INPUT({'id': this.elId + 'Version', 'name': this.elId + 'Version', 'type': 'hidden'}),
        INPUT({'id': this.elId + 'Flavor', 'name': this.elId + 'Flavor', 'type': 'hidden'})
    );
    swapDOM(oldEl, picker);

    if(this.troveName) {
        this.getAllTroveLabels();
    } else {
        this.getGroupTroves();
    }
}

// A flavor has been chosen--continue on
TrovePicker.prototype.pickFlavor = function(e) {
    flavor = e.src().flavor;
    setNodeAttribute($(this.elId + 'Flavor'), 'value', e.src().flavor);
    
    swapDOM($(this.elId + 'selectionList'),
        SPAN(null, e.src().name + "=" + e.src().version + "[" + e.src().flavor + "]"));

    // return to getTroveVersions
    returnLink = A(null, returnImg(), " Back");
    returnLink.version = e.src().version;
    returnLink.label = e.src().label;
    connect(returnLink, "onclick", this, "showTroveFlavors");
    replaceChildNodes($('return'), returnLink);

    var sb = $('submitButton');
    sb.disabled = false;
}

// Show all flavors available for a given trove and version
TrovePicker.prototype.showTroveFlavors = function(e) {
    this.version = e.src().version;
    this.label = e.src().label;
    setNodeAttribute($(this.elId + 'Version'), 'value', this.version);

    oldList = $(this.elId + 'selectionList');
    ul = UL({ 'id': this.elId + 'selectionList' });

    for(var i in this.flavorCache[this.version]) {
        flavor = this.flavorCache[this.version][i];
        link = forwardLink(null, this.flavorDict[flavor]);
        link.name = this.troveName;
        link.version = this.version;
        link.flavor = flavor;
        link.label = this.label;
        connect(link, "onclick", this, "pickFlavor");
        appendChildNodes(ul, link);
    }
    // return to getTroveVersions
    returnLink = A(null, returnImg(), " Back");
    returnLink.label = this.label;
    connect(returnLink, "onclick", this, "getTroveVersions");
    replaceChildNodes($('return'), returnLink);

    swapDOM(oldList, ul);
    this.working(false);
    replaceChildNodes($(this.elId + 'prompt'), "Please choose a flavor:");
}

// Show all versions of a trove on a given label
TrovePicker.prototype.getTroveVersions = function(e) {
    this.label = e.src().label;
    var par = this;
    var key = this.label + "=" + this.troveName;

    var setupList = function(req) {
        var versionDict = req[0];
        var versionList = req[1];
        oldList = $(par.elId + 'selectionList');
        ul = UL({ 'id': par.elId + 'selectionList' });

        par.flavorCache = versionDict;
        par.flavorDict = req[2];

        for(var i in versionList) {
            link = forwardLink(null, versionList[i]);
            link.version = versionList[i];
            link.label = par.label;
            connect(link, "onclick", par, "showTroveFlavors");
            appendChildNodes(ul, link);
        }
        swapDOM(oldList, ul);
        par.working(false);
        replaceChildNodes($(par.elId + 'prompt'), "Please choose a version:");

        // return to getAllTroveLabels
        returnLink = A(null, returnImg(), " Back");
        returnLink.troveName = par.troveName;
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
TrovePicker.prototype.getAllTroveLabels = function(e) {
    if(e) {
        this.troveName = e.src().troveName;
    }
    setNodeAttribute($(this.elId + 'Name'), 'value', this.troveName);
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

TrovePicker.prototype.getGroupTroves = function() {
    var par = this;

    var setupList = function(troveList) {
        oldList = $(par.elId + 'selectionList');
        ul = UL({'id': par.elId + 'selectionList'});

        for(var i in troveList) {
            link = forwardLink(null, troveList[i]);
            link.troveName = troveList[i];
            connect(link, "onclick", par, "getAllTroveLabels");
            appendChildNodes(ul, link);
        }
        swapDOM(oldList, ul);
        par.working(false);
        replaceChildNodes($(this.elId + 'prompt'), "Please choose a group:");
    };


    var callback = function(aReq) {
        logDebug(aReq.responseText);
        troveList = evalJSONRequest(aReq);
        par.troveList = troveList;
        setupList(troveList);
    };

    this.working(true);
    var req = new JsonRpcRequest("jsonrpc/", "getGroupTroves");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(callback);
    req.send(true, [this.projectId]);
}

TrovePicker.prototype.handleError = function() {
    this.working(false);
    oldList = $(this.elId + 'spinnerList');
    ul = UL({'id': this.elId + 'spinnerList'}, LI({'style': 'color: red;'}, "Error connecting to server"));
    swapDOM(oldList, ul);
}
