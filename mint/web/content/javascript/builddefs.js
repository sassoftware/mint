/*
    Copyright (c) 2007 rPath, Inc.
    All Rights Reserved
*/

var RDT_STRING = 0;
var RDT_BOOL = 1;
var RDT_INT = 2;
var RDT_ENUM = 3;
var RDT_TROVE = 4;

function buildTableFromDict(data, baseId) {
    var table = TABLE({'class': 'buildDefs', 'id': baseId});
    for(var key in data) {
        var tr = TR();

        var name = baseId + key;
        var dataRow = data[key];
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

        appendChildNodes(table, tr);
    }

    var cancel = BUTTON({'style':'margin-right: 24px;'}, "Cancel");
    var save = BUTTON({}, "Save");

    connect(cancel, "onclick", function() {
        logDebug("removing " + baseId);
        templateDiv = DIV({'id': 'newType'});
        $("newBuildType").disabled = false;
        $("newBuildButton").disabled = false;


        swapDOM($(baseId), templateDiv);
    });

    appendChildNodes(table, TR({'class': 'dialogButtons'}, TD({'colspan':'2'},
        save, cancel)));

    return table;
}

function addNew() {
    x = $("newBuildType");
    var buildType = x.options[x.selectedIndex].value;
    logDebug("selected build type", buildType);
    var newTable = buildTableFromDict(defaultBuildOpts[buildType], 'new');
    $("newBuildType").disabled = true;
    $("newBuildButton").disabled = true;

    swapDOM($("newType"), newTable);
}
