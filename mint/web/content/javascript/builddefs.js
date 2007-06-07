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
    this.buildType = buildType;
    this.editor = null;
    bindMethods(this);
}

Build.prototype.settings = new Array();

Build.prototype.createRow = function(key, dataRow) {
    var tr = TR();

    var name = this.baseId + key;
    switch(dataRow[0]) {

    case RDT_STRING:
    case RDT_INT:
        appendChildNodes(tr, TD({}, LABEL({'for': name}, dataRow[2])));
        appendChildNodes(tr, TD({}, INPUT({'class': 'text', 'type': 'text', 'name': name, 'id': name, 'value': dataRow[1]})));
        break;
    case RDT_BOOL:
        var td = TD();
        appendChildNodes(td, INPUT({'class': 'reversed', 'value': '1', 'id': name, 'name': name, 'type': 'checkbox'}));
        appendChildNodes(td, LABEL({'for': name}, dataRow[2]));
        appendChildNodes(tr, TD({}), td);
        break;
    case RDT_ENUM:
        appendChildNodes(tr, TD({}, LABEL({'for': name}, dataRow[2])));
        var select = SELECT({'name': name, 'id': name});
        logDebug(dataRow[3]);
        for(enumPrompt in dataRow[3]) {
            var optionDict = {'value': dataRow[3][enumPrompt]};
            if(dataRow[1] == dataRow[3][enumPrompt]) {
                optionDict['selected'] = 'selected';
            }
            appendChildNodes(select, OPTION(optionDict, enumPrompt));
        }

        appendChildNodes(tr, TD({}, select));
        break;
    default:
    }
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


Build.prototype.save = function() {
    var buildSettings = new Array();

    // this is much harder than it should be
    // in python, it would look like this:
    // buildSettings = [dict([(d[0], d[1][1]) for d in build.data.items()]) for build in builds]
    //
    dataArray = map(function(x) { return x.data }, builds);
    for(i in dataArray) {
        if(dataArray.hasOwnProperty(i)) {
            d = {};
            for(j in dataArray[i]) {
                if(dataArray[i].hasOwnProperty(j)) {
                    d[j] = dataArray[i][j][1];
                }
            }
            buildSettings = buildSettings.concat(d);
        }
    }

    setupRows();
    replaceChildNodes($('showJson'), buildSettings.toJSONString());
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
                    TD({}, editLink),
                    TD({}, deleteLink)),
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