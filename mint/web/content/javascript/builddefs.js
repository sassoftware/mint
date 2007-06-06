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

function Build(baseId, data, hideOnCancel) {
    this.baseId = baseId;
    this.data = data;
    this.hideOnCancel = hideOnCancel;
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
    var table = TABLE({'class': 'buildDefs', 'id': 'edit_' + this.baseId});
    hideElement(table);
    for(var key in this.data) {
        appendChildNodes(table, this.createRow(key, this.data[key]));
    }

    var cancel = BUTTON({'style':'margin-right: 24px;'}, "Cancel");
    var save = BUTTON({}, "Save");

    connect(cancel, "onclick", this.cancel);
    connect(save, "onclick", function (){});

    appendChildNodes(table, TR({'class': 'dialogButtons'}, TD({'colspan':'2'},
        save, cancel)));

    this.editor = table;
}

Build.prototype.cancel = function() {
    if(this.hideOnCancel) {
        hideElement(this.editor);
    } else {
        templateDiv = DIV({'id': 'newType'});
        $("newBuildType").disabled = false;
        $("newBuildButton").disabled = false;

        swapDOM(this.editor, templateDiv);
    }
}

function addNew() {
    uniqId++;

    x = $("newBuildType");
    buildType = x.options[x.selectedIndex].value;
    newBuild = new Build(uniqId, defaultBuildOpts[buildType], false);
    $("newBuildType").disabled = true;
    $("newBuildButton").disabled = true;

    newBuild.createEditor();
    showElement(newBuild.editor);
    swapDOM($("newType"), newBuild.editor);
}

function showEdit(baseId) {
    showElement($(baseId));
}

function addExisting(baseId, data) {
    uniqId++;

    newBuild = new Build(uniqId, defaultBuildOpts[data['type']], true);
    newBuild.createEditor();
    swapDOM($('edit_' + baseId), newBuild.editor);
    // don't save this into the main array until "Saved"
}
