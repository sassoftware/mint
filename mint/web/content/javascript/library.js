var staticPath = '/conary-static/';
var BaseUrl = '/';

// user interface helpers ---------------------------------------------------

function toggle_element_by_checkbox(elId, checkId) {
    el = $(elId);
    check = $(checkId);

    logDebug("checked: ", check.checked);
    if(check.checked) {
        showElement(elId);
    } else {
        hideElement(elId);
    }
}

// appends a new item to a select element
function appendToSelect(select, value, content, title, className) {
    var o = document.createElement("option");
    o.value = value;
    o.className = className;
    if (title != '') {
        o.title = (title);
    }
    o.appendChild(content);
    select.appendChild(o);
}

// clears the contents of a selectelement
function clearSelection(select) {
    while (select.length > 0) {
        select.remove(0);
    }
}


function displayCheckList(fieldname, allItems, selectedItems) {
    var anchorFieldname = 'chklist_'+fieldname;
    replaceChildNodes(anchorFieldname, P(null));
    if (allItems.length > 0) {
        for (var i in allItems) {
            var idname = anchorFieldname + '_' + i;
            var attrs = {'id': idname, 'class': 'check indented groupcheck', 'type': 'checkbox', 'name': fieldname, 'value': allItems[i]};
            if (selectedItems) {
                if (selectedItems.indexOf(allItems[i]) >= 0) {
                    attrs['checked'] = 'checked';
                }
            }
            appendChildNodes(anchorFieldname, INPUT(attrs, null),
                    LABEL({'for': idname}, allItems[i]), BR(null));
        }
        appendChildNodes(anchorFieldname, P(null));
        return true;
    }
    else {
        return false;
    }
}

function getGroups(projId, selectedGroups) {
    var processShowGroups = function (aReq) {
        logDebug(aReq.responseText);
        troveList = evalJSONRequest(aReq);
        displayCheckList('groups', troveList, selectedGroups);
    }
    replaceChildNodes('chklist_groups');
    if (projId < 0) {
        return;
    }
    appendChildNodes('chklist_groups', P({'class': 'indented'}, IMG({'src': staticPath + 'apps/mint/images/circle-ball-dark-antialiased.gif'}), "Retrieving groups..."));
    var req = new JsonRpcRequest("jsonrpc/", "getGroupTroves");
    req.setCallback(processShowGroups);
    req.send(true, [parseInt(projId)]);
}

function callbackVoid() {}

// RPC callbacks ------------------------------------------------------------

function addOutboundMirror_setUseReleases (value) {
    // Update radio buttons for useReleases
    $('useReleases').checked = value ? "checked" : "";
    $('useLabels').checked = value ? "" : "checked";

    // Disable the other elements if useReleases is on
    var elements = ['allLabels', 'selectLabels', 'mirrorByLabel', 'mirrorByGroup', 'mirrorSources'];
    for (var i in elements)
        $(elements[i]).disabled = value ? "disabled" : "";
}

function addOutboundMirror_setMirrorByGroup(value) {
    $('mirrorSources').disabled = value ? "disabled" : "";
}

// RPC calls ----------------------------------------------------------------

function reloadCallback() {
    window.location.replace(document.URL);
    // Needed for Safari to reload properly.  Weird.
    setTimeout('window.location.reload()', 0);
}

function setMirrorOrder(table, id, order) {
    var req = new JsonRpcRequest("jsonrpc/", "set" + table + "Order");
    req.setCallback(reloadCallback);
    req.send(true, [id, order]);
}

function getProjectLabels(projectId, selectedProjectLabels) {

    projLabelsCallback = function(aReq) {
        var labels = evalJSONRequest(aReq);
        displayCheckList('labelList', labels, selectedProjectLabels);
    }

    replaceChildNodes('chklist_labelList');
    if (projectId < 0) {
        return;
    }
    appendChildNodes('chklist_labelList', P({'class': 'indented'}, IMG({'src': staticPath + 'apps/mint/images/circle-ball-dark-antialiased.gif'}), "Retrieving labels..."));
    var req = new JsonRpcRequest('jsonrpc/', 'getAllProjectLabels');
    req.setCallback(projLabelsCallback);
    req.send(true, [parseInt(projectId)]);
}

function addOutboundMirror_onProjectChange (e) {
    getProjectLabels(e.src().value);
    getGroups(e.src().value);
    if (e.src().value > 0) {
        $('submitButton').disabled = false;
    } else {
        $('submitButton').disabled = true;
    }
}

function addOutboundMirror_onUseReleases (e) {
    if (e.src().id == 'useReleases')
        addOutboundMirror_setUseReleases(true);
    else
        addOutboundMirror_setUseReleases(false);
}

function addOutboundMirror_onMirrorByGroup(e) {
    if (e.src().id == 'mirrorByGroup')
        addOutboundMirror_setMirrorByGroup(true);
    else
        addOutboundMirror_setMirrorByGroup(false);
}
