//
// Copyright (C) 2006 rPath, Inc
// All Rights Reserved
//

var labelsCache = {};
var versionCache = {};
var flavorCache = {};

var staticPath = '';

var green = {'style': 'color: green; font-weight: bold;'};
var gray = {'style': 'color: gray;'};

var spinnerImg = 'apps/mint/images/circle-ball-dark-antialiased.gif';
var nextImg = 'apps/mint/images/next.gif';
var prevImg = 'apps/mint/images/prev.gif';
var prevImgDisabled = 'apps/mint/images/prev_disabled.gif';

// Helper functions
function working(isWorking) {
    if(isWorking) {
        showElement('spinnerList');
        hideElement('selectionList');
    }
    else {
        hideElement('spinnerList');
        showElement('selectionList');
    }
}

function forwardLink(attrs, text) {
    return LI(null, A(attrs, IMG({'src': staticPath + nextImg}), " " + text));
}

function returnImg() {
    return IMG({'src': staticPath + prevImg});
}

function disabledReturn() {
    return DIV(gray, IMG({'src': staticPath + prevImgDisabled}), " Return");
}

function buildTroveSpec(name, version, flavor) {
    return DIV({'id': 'troveSpec'},
        DIV((name ? green : gray), "Name: ", name),
        DIV((version ? green : gray), "Version: ", version),
        DIV((flavor ? green : gray), "Flavor: ", flavor)
    );
}

// Build the initial DOM for the trove picker and
// begin retrieving all leaves for a given
// trove name on a server.
function buildTrovePicker(serverName, troveName, pickerId, mintStaticPath) {
    staticPath = mintStaticPath;

    oldEl = $(pickerId);
    picker = DIV({'id': pickerId, 'class': 'trovePicker'})
    spinner = UL({'id': 'spinnerList'},
        LI(null, "Loading...", IMG({'src': staticPath + spinnerImg}))
    );
    appendChildNodes(picker, SPAN({'id': 'prompt'}),
        P({'style': 'float: right;'}, SPAN({'id': 'next'}, null), " ", IMG({'src': staticPath + nextImg})),
        P({'id': 'return'}),
        spinner,
        UL({'id': 'selectionList'}),
        buildTroveSpec('', '', '')
    );
    swapDOM(oldEl, picker);
    getAllTroveLabels(serverName, troveName);
}

// Show all flavors available for a given trove and version
function showTroveFlavors(troveName, version, label, serverName) {
    replaceChildNodes($('troveSpec'), buildTroveSpec(troveName, version, ''));
    oldList = $('selectionList');
    ul = UL({ 'id': 'selectionList' });

    for(var i in flavorCache[version]) {
        flavor = flavorCache[version][i];
        attrs = {'onclick': 'getTroveFlavor("' + versionList[i] + '", "' + troveName + '");'};
        appendChildNodes(ul, forwardLink(attrs, flavor));

        // return to getTroveVersions
        returnLink = A({'onclick': 'getTroveVersions("' + label + '", "' + troveName + '", "' + serverName + '");'}, returnImg(), " Return");
        replaceChildNodes($('return'), returnLink);
    }
    swapDOM(oldList, ul);
    working(false);
    replaceChildNodes($('prompt'), "Please choose a flavor:");
}

// Show all versions of a trove on a given label
function getTroveVersions(label, troveName, serverName) {
    var key = label + "=" + troveName;

    var setupList = function(versionList) {
        oldList = $('selectionList');
        ul = UL({ 'id': 'selectionList' });

        flavorCache = versionList;
        for(var i in versionList) {
            attrs = {'onclick': 'showTroveFlavors("' + troveName + '", "' + i + '", "' + label + '", "' + serverName + '");'};
            appendChildNodes(ul, forwardLink(attrs, i));
        }
        swapDOM(oldList, ul);
        working(false);
        replaceChildNodes($('prompt'), "Please choose a version:");
        replaceChildNodes($('next'), "Next: Choose a Version");
        replaceChildNodes($('next'), "Next: Choose a Flavor");
        replaceChildNodes($('troveSpec'), buildTroveSpec(troveName, label, ''));

        // return to getAllTroveLabels
        replaceChildNodes($('return'),
            A({'onclick': 'getAllTroveLabels("' + serverName + '", "' + troveName + '", "' + label + '");'},
            returnImg(), " Return")
        );
    };

    var callback = function(aReq) {
        logDebug("[JSON] response: ", aReq.responseText);

        versionList = evalJSONRequest(aReq);
        versionCache[key] = versionList;
        setupList(versionList);
    }

    if(!versionCache[key]) {

        working(true);
        var req = new JsonRpcRequest("jsonrpc/", "getTroveVersions");
        req.setCallback(callback);
        req.send(true, [label, troveName]);
    } else {
        setupList(versionCache[key]);
    }
}

// Fetch all labels a trove exists on a given server
function getAllTroveLabels(serverName, troveName) {
    var key = serverName + "=" + troveName;

    var setupList = function(labelList) {
        oldList = $('selectionList');
        ul = UL({ 'id': 'selectionList' });

        for(var i in labelList) {
            attrs = {'onclick': 'getTroveVersions("' + labelList[i] + '", "' + troveName + '", "' + serverName + '");'};
            appendChildNodes(ul, forwardLink(attrs, labelList[i]));
        }
        swapDOM(oldList, ul);
        working(false);
        replaceChildNodes($('prompt'), "Please choose a label:");
        replaceChildNodes($('next'), "Next: Choose a Version");
        replaceChildNodes($('troveSpec'), buildTroveSpec(troveName, serverName, ''));
        replaceChildNodes($('return'), disabledReturn());
    };

    var callback = function(aReq) {
        logDebug("[JSON] response: ", aReq.responseText);

        labelList = evalJSONRequest(aReq);
        labelsCache[key] = labelList;
        setupList(labelList);
    };

    if(!labelsCache[key]) {
        working(true);
        var req = new JsonRpcRequest("jsonrpc/", "getAllTroveLabels");
        req.setAuth(getCookieValue("pysid"));
        req.setCallback(callback);
        req.send(true, [serverName, troveName]);
    } else {
        setupList(labelsCache[key]);
    }
}
