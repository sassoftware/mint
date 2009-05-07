//
// Copyright (C) 2006-2008 rPath, Inc
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

function buildTroveSpec(n, v, f) {
    var ts = n + "=" + v;
    // flavor may be null for "all flavors"
    if(f) {
        ts += "[" + f + "]";
    }

    return ts;
}

function trailingRevision(v) {
    var parts = v.split(":");
    var revision = parts[parts.length-1];
    return revision;
}

// ctor
function TrovePicker(projectId, serverName, troveName, pickerId, mintStaticPath, 
                     allowNone, forceAllFlavors) {
    this.projectId = projectId;
    this.serverName = serverName;
    this.troveName = troveName;
    this.elId = pickerId;
    staticPath = mintStaticPath;
    this.allowNone = allowNone;
    this.forceAllFlavors = forceAllFlavors;

    if(troveName) {
        this.allowNameChoice = false;
    }

    this.buildTrovePicker();
}

TrovePicker.prototype.troveName = null;
TrovePicker.prototype.serverName = null;
TrovePicker.prototype.label = null;
TrovePicker.prototype.version = null;
TrovePicker.prototype.flavorCache = null;
TrovePicker.prototype.domCache = {};
TrovePicker.prototype.allowNameChoice = true;
TrovePicker.prototype.allowNone = false;
TrovePicker.prototype.archFilter = Array();
TrovePicker.prototype.flavFilter = Array();
TrovePicker.prototype.buildChange = null;
TrovePicker.prototype.stage = null;
TrovePicker.prototype.customSpec = null;
TrovePicker.prototype.forceAllFlavors = false;

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
    this.stage = 'group';
    var oldEl = $(this.elId);
    var picker = DIV({'id': this.elId, 'class': 'trovePicker'});
    var spinner = UL({'id': this.elId + 'spinnerList'},
        LI(null, "Loading...", IMG({'src': staticPath + spinnerImg}))
    );
    appendChildNodes(picker, SPAN({'id': this.elId + 'prompt', 'class': 'prompt'}),
        P({'id': this.elId + 'return'}),
        spinner,
        UL({'id': this.elId + 'selectionList'}),
        INPUT({'id': this.elId.replace("-", "_") + 'Spec', 'name': this.elId + 'Spec', 'type': 'hidden'})
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
    this.stage = 'finish';
    var n = e.src().name;
    var v = e.src().version;
    var shortv = trailingRevision(v);
    var f = e.src().flavor;
    var shortf = e.src().shortFlavor;

    var troveSpec = buildTroveSpec(n, v, f);
    setNodeAttribute($(this.elId.replace("-", "_") + 'Spec'), 'value', troveSpec);

    oldEl = $(this.elId + 'selectionList');
    newEl = DIV({'id': this.elId + 'selectionList'},
        SPAN({'style': 'font-weight: bold;'}, 'Group: '),
        SPAN(null, n + "=" + shortv + " [" + shortf + "]")
    );
    swapDOM(oldEl, newEl);

    // return to getTroveVersions
    returnLink = A(null, returnImg(), " Back");
    returnLink.troveName = n;
    returnLink.version = e.src().version;
    returnLink.label = e.src().label;
    connect(returnLink, "onclick", this, "showTroveFlavors");
    replaceChildNodes($(this.elId + 'return'), returnLink);
    replaceChildNodes($(this.elId + 'prompt'), "Selected group:");

    var sb = $('submitButton');
    sb.disabled = false;
    if(this.elId == "distTrove") {
        handleBuildTypes(f);
    }
}

TrovePicker.prototype.pickNoTrove = function(e) {
    setNodeAttribute($(this.elId.replace("-", "_") + 'Spec'), 'value', 'NONE');
    var n = e.src().troveName;

    oldEl = $(this.elId + 'selectionList');
    newEl = DIV({'id': this.elId + 'selectionList'},
        SPAN({'style': 'font-weight: bold;'}, 'Group: '),
        SPAN(null, "No " + n + " will be used for this build.")
    );
    swapDOM(oldEl, newEl);

    // return to getTroveVersions
    returnLink = A(null, returnImg(), " Back");
    returnLink.troveName = n;
    connect(returnLink, "onclick", this, "getAllTroveLabels");
    replaceChildNodes($(this.elId + 'return'), returnLink);
    var sb = $('submitButton');
    sb.disabled = false;
}

// Display flavors in the dom
TrovePicker.prototype.displayFlavors = function() {
    oldList = $(this.elId + 'selectionList');
    ul = UL({ 'id': this.elId + 'selectionList' });
    
    if(this.forceAllFlavors) {
        var myId = "flavorId" + 0;
        link = forwardLink({'id': myId}, 'All Flavors');
        link.name = this.troveName;
        link.version = this.version;
        link.flavor = null;  //we want all flavors
        link.shortFlavor = 'All Flavors';
        link.label = this.label;
        connect(link, "onclick", this, "pickFlavor");
        appendChildNodes(ul, link);
    } else {
	    for(var i in this.flavorCache[this.version]) {
	        var omitFlavor = false;
	        // Filter by arch
	        for (var j in this.archFilter) {
	            if (String(this.flavorCache[this.version][i]).match(this.archFilter[j]) != null) {
	                omitFlavor = true;;
	            }
	        }
	        // Filter by flavor
	        for (var j in this.flavFilter) {
	            if (String(this.flavorCache[this.version][i]).split(',').indexOf(this.flavFilter[j]) != -1) {
	                omitFlavor = true;
	            }
	        }
	        if (omitFlavor) {
	            continue;
	        }
	        flavor = this.flavorCache[this.version][i];
	        var myId = "flavorId" + i;
	        link = forwardLink({'id': myId}, flavor[0]);
	        link.name = this.troveName;
	        link.version = this.version;
	        link.flavor = flavor[1];
	        link.shortFlavor = flavor[0];
	        link.label = this.label;
	        connect(link, "onclick", this, "pickFlavor");
	        appendChildNodes(ul, link);
	    }
	}
    swapDOM(oldList, ul);
}

// Show all flavors available for a given trove and version
TrovePicker.prototype.showTroveFlavors = function(e) {
    this.stage = 'flavor';
    this.version = e.src().version;
    this.label = e.src().label;

    this.displayFlavors();
    // return to getTroveVersions
    returnLink = A(null, returnImg(), " Back");
    returnLink.label = this.label;
    connect(returnLink, "onclick", this, "getTroveVersions");
    replaceChildNodes($(this.elId + 'return'), returnLink);

    this.working(false);
    replaceChildNodes($(this.elId + 'prompt'), "Please choose a flavor:");
    enableAllBuildTypes();
}

// Show all versions of a trove on a given label
TrovePicker.prototype.getTroveVersions = function(e) {
    this.stage = 'version';
    this.label = e.src().label;
    var par = this;
    var key = this.label + "=" + this.troveName;

    var sb = $('submitButton');
    sb.disabled = true;

    var setupList = function(req) {
        var versionDict = req[0];
        var versionList = req[1];
        oldList = $(par.elId + 'selectionList');

        par.flavorCache = versionDict;

        if(!par.domCache[key] || par.buildChange) {
            ul = UL({ 'id': par.elId + 'selectionList' });
            for(var i in versionList) {
                link = forwardLink(null, trailingRevision(versionList[i]));
                link.version = versionList[i];
                link.label = par.label;
                connect(link, "onclick", par, "showTroveFlavors");
                appendChildNodes(ul, link);
            }
            par.domCache[key] = ul;
            par.buildChange = 'false';
        }
        swapDOM(oldList, par.domCache[key]);

        par.working(false);
        replaceChildNodes($(par.elId + 'prompt'), "Please choose a version:");

        // return to getAllTroveLabels
        returnLink = A(null, returnImg(), " Back");
        returnLink.troveName = par.troveName;
        connect(returnLink, "onclick", par, "getAllTroveLabels");
        replaceChildNodes($(par.elId + 'return'), returnLink);
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
        req.setAuth(getCookieValue("pysid"));
        req.setCallback(callback);
        req.send(true, [this.projectId, this.label, this.troveName]);
    } else {
        setupList(versionCache[key]);
    }
}

// Show a textbox in which to enter an exact version
TrovePicker.prototype.getCustomVersion = function(e) {
    this.stage = 'custom_version';

    var sb = $('submitButton');
    sb.disabled = true;

    oldList = $(this.elId + 'selectionList');
    newList = UL({ 'id': this.elId + 'selectionList' });

    label = LI({'style': 'font-size: 80%'},
        "Example: foobar=example.com@rpl:1[is: x86]");

    input = LI(null, INPUT({ 'id': this.elId + 'customInput', 'value': this.customSpec }));
    this.customSpec = null;

    link = forwardLink(null, "OK");
    connect(link, "onclick", this, "pickCustomVersion");

    appendChildNodes(newList, label, input, link);

    this.working(false);
    swapDOM(oldList, newList);
    replaceChildNodes($(this.elId + 'prompt'), "Please enter a trovespec:");

    // return to getAllTroveLabels
    returnLink = A(null, returnImg(), " Back");
    returnLink.troveName = this.troveName;
    connect(returnLink, "onclick", this, "getAllTroveLabels");
    replaceChildNodes($(this.elId + 'return'), returnLink);

}

TrovePicker.prototype.pickCustomVersion = function(e) {
    this.customSpec = $(this.elId + 'customInput').value;
    setNodeAttribute($(this.elId.replace("-", "_") + 'Spec'), 'value', this.customSpec);

    oldEl = $(this.elId + 'selectionList');
    newEl = DIV({'id': this.elId + 'selectionList'},
        SPAN({'style': 'font-weight: bold;'}, 'Trove: '),
        SPAN(null, this.customSpec)
    );
    swapDOM(oldEl, newEl);

    // return to getCustomVersion
    returnLink = A(null, returnImg(), " Back");
    connect(returnLink, "onclick", this, "getCustomVersion");
    replaceChildNodes($(this.elId + 'return'), returnLink);
    var sb = $('submitButton');
    sb.disabled = false;
}

// Fetch all labels a trove exists on a given server
TrovePicker.prototype.getAllTroveLabels = function(e) {
    this.stage = 'label';
    if(e) {
        this.troveName = e.src().troveName;
    }
    var key = this.serverName + "=" + this.troveName;
    var par = this; // save the parent for the subfunction's use

    var sb = $('submitButton');
    sb.disabled = true;

    var setupList = function(labelList) {
        oldList = $(par.elId + 'selectionList');
        ul = UL({ 'id': par.elId + 'selectionList' });

        if(labelList.length < 1) {
            appendChildNodes(ul, LI(null, "No " + par.troveName + " packages found"));
        }
        for(var i in labelList) {
            link = forwardLink(null, labelList[i]);
            link.label = labelList[i];
            connect(link, "onclick", par, "getTroveVersions");
            appendChildNodes(ul, link);
        }
        if(par.elId != 'distTrove') {
            link = forwardLink(null, "Custom");
            connect(link, "onclick", par, "getCustomVersion");
            appendChildNodes(ul, link);
        }
        if(par.allowNone) {
            link = forwardLink(null, "Do not use " + par.troveName + " for this build.");
            link.troveName = par.troveName;
            connect(link, "onclick", par, "pickNoTrove");
            appendChildNodes(ul, link);
        }
        swapDOM(oldList, ul);
        par.working(false);
        replaceChildNodes($(par.elId + 'prompt'), "Please choose a label:");

        if(par.allowNameChoice) {
            // return to getGroupTroves
            returnLink = A(null, returnImg(), " Back");
            connect(returnLink, "onclick", par, "getGroupTroves");
            replaceChildNodes($(par.elId + 'return'), returnLink);
        } else {
            replaceChildNodes($(par.elId + 'return'), disabledReturn());
        }
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
    this.stage = 'group';
    var par = this;

    var sb = $('submitButton');
    sb.disabled = true;
    var setupList = function(troveList) {
        oldList = $(par.elId + 'selectionList');
        ul = UL({'id': par.elId + 'selectionList'});

        if(troveList.length < 1) {
            appendChildNodes(ul, LI(null, "No groups found. Cook a group and try again."));
        }
        for(var i in troveList) {
            link = forwardLink(null, troveList[i]);
            link.troveName = troveList[i];
            connect(link, "onclick", par, "getAllTroveLabels");
            appendChildNodes(ul, link);
        }
        swapDOM(oldList, ul);
        par.working(false);
        replaceChildNodes($(par.elId + 'prompt'), "Please choose a group:");
        replaceChildNodes($(par.elId + 'return'), disabledReturn());
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

TrovePicker.prototype.filterFlavors = function(t) {
    if (x86_64Types.indexOf(t) == -1) {
        this.archFilter = Array('x86_64');
    }
    else {
        this.archFilter = Array();
    }

    if (xenTypes.indexOf(t) == -1) {
        this.flavFilter = Array('domU');
    }
    else {
        this.flavFilter = Array();
    }
    this.buildChange = true;
    if (this.stage == 'flavor') {
        this.displayFlavors();
    }
}

var allTypes = map(parseInt, keys(buildTypeNames));

var defaultType = INSTALLABLE_ISO;
var x86_64Types = allTypes;
var xenTypes = [INSTALLABLE_ISO, RAW_FS_IMAGE, RAW_HD_IMAGE, TARBALL, XEN_OVA,
                AMI, IMAGELESS];

function handleBuildTypes(flavor) {
    forEach(allTypes, function(x) {
        var el = $('buildtype_' + x);
        var elLabel = $('buildtype_' + x + '_label');
        if(el) {
            el.disabled = false;
            setOpacity(elLabel, 1.0);
        }
    });

    if(flavor) {
        // bootableTypes are not currently compatible with x86_64
        // so, if that arch was selected, disable it:
        selectiveDisableArch(flavor, "x86_64", x86_64Types);

        // only allow a few build types to be built from a xen flavor:
        selectiveDisable(flavor, "domU", xenTypes);
    }
}


function selectiveDisableArch(flavor, flavorMatch, allowed) {
    if(flavor.match(flavorMatch)) {
        one = iter(allTypes);
        forEach(one, function (x) {
            var el = $('buildtype_'+x);
            var elLabel = $('buildtype_' + x + '_label');
            if(el) {
                if (findValue(allowed, x) == -1) {
                    el.disabled = true;
                    setOpacity(elLabel, 0.5);
                }
            }
        });
    }
}

function selectiveDisable(flavor, flavorMatch, allowed) {
    var flavors = flavor.split(',');
    if(flavors.indexOf(flavorMatch) != -1) {
        one = iter(allTypes);
        forEach(one, function (x) {
            var el = $('buildtype_'+x);
            var elLabel = $('buildtype_' + x + '_label');
            if(el) {
                if (findValue(allowed, x) == -1) {
                    el.disabled = true;
                    setOpacity(elLabel, 0.5);
                }
            }
        });
    }
}

function enableAllBuildTypes() {
    one = iter(allTypes);
    forEach(one, function (x) {
        var el = $('buildtype_'+x);
        var elLabel = $('buildtype_' + x + '_label');
        if(el) {
            el.disabled = false;
            setOpacity(elLabel, 1.0);
        }
    });
    var sb = $('submitButton');
    sb.disabled = true;
}
