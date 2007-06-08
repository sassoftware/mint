/*
    Copyright (c) 2007 rPath, Inc.
    All Rights Reserved
*/

var RDT_STRING = 0;
var RDT_BOOL = 1;
var RDT_INT = 2;
var RDT_ENUM = 3;
var RDT_TROVE = 4;

var builds = new Array();
var uniqId = 0;

function Build(baseId, buildType) {
    logDebug("new build of type " + buildType);
    this.baseId = baseId;
    this.data = defaultBuildOpts[buildType];
    this.buildType = Number(buildType);
    this.editor = null;
    bindMethods(this);
}

Build.prototype.settings = new Array();
Build.prototype.enumEls = new Array();

Build.prototype.createRow = function(key, dataRow) {
    var tr = TR();

    var name = this.baseId + key;
    var input;
    switch(dataRow[0]) {

    case RDT_STRING:
    case RDT_INT:
        input = INPUT({'class': 'text', 'type': 'text', 'name': name, 'id': name, 'value': dataRow[1]});
        appendChildNodes(tr, TD({}, LABEL({'for': name}, dataRow[2])));
        appendChildNodes(tr, TD({}, input));
        break;
    case RDT_BOOL:
        var td = TD();
        input = INPUT({'class': 'reversed', 'value': '1', 'id': name, 'name': name, 'type': 'checkbox'});
        appendChildNodes(td, input);
        appendChildNodes(td, LABEL({'for': name}, dataRow[2]));
        appendChildNodes(tr, TD({}), td);
        break;
    case RDT_ENUM:
        appendChildNodes(tr, TD({}, LABEL({'for': name}, dataRow[2])));
        var select = SELECT({'name': name, 'id': name});
        this.enumEls[key] = new Array();
        for(enumPrompt in dataRow[3]) {
            if(dataRow[3].hasOwnProperty(enumPrompt)) {
                var optionDict = {'value': dataRow[3][enumPrompt]};
                if(dataRow[1] == dataRow[3][enumPrompt]) {
                    optionDict['selected'] = 'selected';
                }
                var option = OPTION(optionDict, enumPrompt);
                this.enumEls[key] = this.enumEls[key].concat(option);
                appendChildNodes(select, option);
            }
        }
        input = select;
        appendChildNodes(tr, TD({}, select));
        break;
    default:
    }
    this.settings[key] = input;
    return tr;
}

Build.prototype.createEditor = function() {
    logDebug("creating editor");
    var table = TABLE({'class': 'buildDefs', 'id': 'edit_' + this.baseId});
    hideElement(table);
    for(var key in this.data) {
        if(this.data.hasOwnProperty(key))
            appendChildNodes(table, this.createRow(key, this.data[key]));
    }

    var cancel = BUTTON({'style':'margin-right: 24px;'}, "Cancel");
    var save = BUTTON({}, "Save");

    connect(cancel, "onclick", this.cancel);
    connect(save, "onclick", this.save);

    appendChildNodes(table, TR({'class': 'dialogButtons'}, TD({'colspan':'2'},
        save, cancel)));

    this.editor = table;
}

Build.prototype.cancel = function() {
    hideElement(this.editor);
}

Build.prototype.showBuild = function() {
    if(!this.editor) {
        this.createEditor();
        swapDOM($('edit_' + this.baseId), this.editor);
    }
    logDebug("showing: edit_" + this.baseId);
    showElement("edit_" + this.baseId);
}

Build.prototype.deleteBuild = function() {
    var idx = builds.indexOf(this);
    builds.splice(idx, 1);
    setupRows();
}

Build.prototype.hide = function() {
    hideElement("edit_" + this.baseId);
}

function getSettings() {
    var buildSettings = new Array();

    buildSettings[0] = {'troveName': 'group-dist', 'name': 'Test Build'};

    for(buildId in builds) {
        if(builds.hasOwnProperty(buildId)) {
            var dataArray = builds[buildId].data;

            var buildInfo = {};
            buildInfo['data'] = {};
            for(settingKey in dataArray) {
                if(dataArray.hasOwnProperty(settingKey)) {
                    var settingType = builds[buildId]['data'][settingKey][0];
                    var el = builds[buildId].settings[settingKey];
                    if(el) { // editor exists, pull value from the editor field
                        switch(settingType) {
                            case RDT_STRING:
                            case RDT_INT:
                                buildInfo['data'][settingKey] = el.checked;
                                break;
                            case RDT_BOOL:
                                buildInfo['data'][settingKey] = el.value;
                                break;
                            case RDT_ENUM:
                                var optionEl = this.enumEls[settingKey][el.selectedIndex];
                                buildInfo['data'][settingKey] = optionEl.value;
                                break;
                            default:
                                logDebug("unknown setting datatype: " + settingType);
                        }
                    } else { // editor not opened yet, just take the default
                        buildInfo['data'][settingKey] = builds[buildId]['data'][settingKey][1];
                    }
                }
            }
            buildInfo['type'] = builds[buildId].buildType;
            buildSettings = buildSettings.concat(buildInfo);
        }
    }
    return buildSettings;
}

Build.prototype.save = function() {
    this.hide();
}

function setupRows() {
    var oldBody = $('buildRowsBody');
    var newBody = TBODY({'id': 'buildRowsBody'});
    for(var i in builds) {
        if(builds.hasOwnProperty(i)) {
            var build = builds[i];

            var editLink = A({'href': '#'}, "Settings");
            var deleteLink = A({'href': '#'}, "Delete");

            connect(editLink, "onclick", build.showBuild);
            connect(deleteLink, "onclick", build.deleteBuild);

            var editor;
            if(build.editor) {
                editor = build.editor;
            } else {
                editor = DIV({'id': 'edit_' + build.baseId});
            }

            appendChildNodes(newBody,
                TR({},
                    TD({}, buildTypeNames[build.buildType]),
                    TD({'style': 'text-align: right;'}, editLink),
                    TD({'style': 'text-align: right; margin-left: 2em;'}, deleteLink)),
                TR({},
                    TD({'colspan': '3'}, editor))
            );
        }
    }
    swapDOM(oldBody, newBody);
}

function addNew() {
    uniqId++;

    var x = $("newBuildType");
    var buildType = x.options[x.selectedIndex].value;
    var newBuild = new Build(uniqId, buildType);
    builds = builds.concat(newBuild);
    setupRows();
}

function addExisting(baseId, data) {
    var newBuild = new Build(baseId, data['type']);
    builds = builds.concat(newBuild);
    uniqId = baseId;
}

function setAlert(text, color, timeout) {
    var newAlert = SPAN({'id': 'alert', 'style': 'padding-right: 1em; float: right; color: '+ color + ';'}, text);
    swapDOM($('alert'), newAlert);

    callLater(timeout, function() {
        swapDOM($('alert'), SPAN({'id': 'alert', 'style': 'float: right;'}));
    });
}

function saveChanges(buildAll) {
    var prefix;
    var func;
    if(buildAll) {
        prefix = "buildAll";
        func = "commitAndBuild";
    } else {
        prefix = "saveChanges";
        func = "commitBuildJson";
    }

    removeElementClass($(prefix + "Spinner"), "invisible");
    $(prefix + "Button").disabled = true;

    var callback = function(r) {
        if(r.responseText != "false") { // error occurred
            setAlert("Error", "red", 5); // TODO: give more information
        } else {
            setAlert("Saved", "green", 2);
        }
    }

    var errback = function() {
        setAlert("Error", "red", 5);
    }

    var finalize = function() {
        addElementClass($(prefix + "Spinner"), "invisible");
        $(prefix + "Button").disabled = false;
    }

    var req = new JsonRpcRequest(BaseUrl + "jsonrpc/", func);
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(bind(callback, this));
    req.setErrback(bind(errback, this));
    req.setFinalizer(bind(finalize, this));
    req.send(true, [ProjectId, LabelStr, getSettings().toJSONString()]);
}
