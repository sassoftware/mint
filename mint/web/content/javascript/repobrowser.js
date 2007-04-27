//
// Copyright (C) 2007 rPath, Inc
// All Rights Reserved
//

function treeInit(treeDiv, verList, selectedLabel) {
    var tree = new YAHOO.widget.TreeView(treeDiv);
    var root = tree.getRoot();
    for (var label in verList) {
        var newNode = new YAHOO.widget.TextNode(label, root, false);
        if (label == selectedLabel) {
            newNode.labelStyle = 'bold';
            newNode.expanded = true;
        }
        for (var rev in verList[label]) {
            var revNode = new YAHOO.widget.TextNode(verList[label][rev][0], newNode, false);
            revNode.href = verList[label][rev][1];
            revNode.labelStyle = verList[label][rev][2];
        }
    }
    tree.draw();
}

function buildHTMLNode (version) {
    if (version[2]) {
        var nameShort = '<a href="' + version[2] + '">' + version[1] + '</a>'; 
        var nameLong = '<a href="' + version[2] + '">' + version[0] + '</a>';
    }
    else {
        var nameShort = '<span>' + version[1] + '</span>';
        var nameLong = '<span>' + version[0] + '</span>';
    }

    var node = '<div id="short' + version[0] + '">' +
               nameShort +
               '<span class="expand" onclick="swapDisplay(\'short' + 
               version[0] + '\', \'long' + version[0] + '\');">' + 
               ' ' + '</span>' +
               '</div>' +
               '<div id="long' + version[0] + '" style="display: none;">' +
               nameLong +
               '<span class="collapse" onclick="swapDisplay(\'long' +
               version[0] + '\', \'short' + version[0] + '\');">' + 
               ' ' + '</span>' +
               '</div>';
    return node;
}

function initVersionTree(lineage) {
    //If this is not a clone or shadow, do nothing
    if (getElement('versionTree') == null) {
        return;
    }

    var verTree = new YAHOO.widget.TreeView('versionTree');
    var root = verTree.getRoot();
    for (var i in lineage) {
        var node = buildHTMLNode(lineage[i]);
        var newNode = new YAHOO.widget.HTMLNode(node, root, false, true);
        root = newNode;
    }
    verTree.draw();
}

function swapDisplay(hideDiv, showDiv) {
    getElement(hideDiv).style.display = 'none';
    getElement(showDiv).style.display = '';
}
