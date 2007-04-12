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

function swapDisplay(hideDiv, showDiv) {
    getElement(hideDiv).style.display = 'none';
    getElement(showDiv).style.display = '';
}
