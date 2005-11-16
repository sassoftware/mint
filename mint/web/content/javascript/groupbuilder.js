/*
 Copyright (c) 2005 rPath Inc.
 All rights reserved

On pages that allow for group manipulation do the following:
    On page load:
        Find the links (which currently add/delete via URLs) replace with javascript ajax commands
            addGroupTrove
            deleteGroupTrove
        Find the template item to use in updating, store it in a javascript object, and remove it from the display
        
    On link click:
        Post the xmlrpc request to add/delete the trove
        Wait for the return value
        Populate the box with the new data returned from the xmlrpc call

    TODO:
        Sorting of the list
*/

function GroupTroveItem(item) {
    bindMethods(this);
    this.item = item;
}

/* Initialization function
*/
function GroupTroveManager() {
    bindMethods(this);
    this.tableNode = getElement('groupbuilder-tbody');
    var exampleNode = getElement('groupbuilder-example');
    //NOTE, don't pull this until after the LinkManager has executed
    this.exampleNode = exampleNode.cloneNode(true);
    //wipe the style attribute that keeps this node hidden
    this.exampleNode.style.display="";
    //Delete the template node
    swapDOM(exampleNode, null);
}

GroupTroveManager.prototype.addTrove = function (url, id, name, version, versionLock, referer) {
    /* Form up the xmlrpc call and add this trove. 
    */
    logDebug('Creating the addTrove xmlrpc request object');
    var req = new XmlRpcRequest(url, 'addGroupTroveItem');
    req.setAuth(getCookieValue("pysid"));
    req.setHandler(this.troveAdded, {'id': id, 'name': name, 'version': version, 'versionLock': versionLock, 'referer': referer});
    logDebug("Sending the request");
    req.send(id, name, version, '', '', Boolean(versionLock), false, false);
}

GroupTroveManager.prototype.addTroveByProject = function (url, id, name, projectName, versionLock, referer) {
    /* Form up the xmlrpc call and add this trove.
    */
    logDebug('Creating the addTroveByProject xmlrpc request object');
    var req = new XmlRpcRequest(url, 'addGroupTroveItemByProject');
    req.setAuth(getCookieValue("pysid"));
    req.setHandler(this.troveAddedByProject, {'id': id, 'name': name, 'projectName': projectName, 'versionLock': versionLock, 'referer': referer});
    logDebug("Sending the request");
    req.send(id, name, projectName, '', '', Boolean(versionLock), false, false);
}

GroupTroveManager.prototype.deleteTrove = function(url, id, troveId) {
    logDebug('Creating the deleteTrove xmlrpc request object');
    var req = new XmlRpcRequest(url, 'delGroupTroveItem');
    log("Cookie value: " + getCookieValue('pysid'));
    req.setAuth(getCookieValue("pysid"));
    req.setHandler(this.troveDeleted);
    logDebug("Sending the request");
    req.send(troveId);
}

GroupTroveManager.prototype.createTroveRow = function(data) {
    logDebug("createTroveRow");
    newRow = this.exampleNode.cloneNode(true);
    logDebug("New row created");
    newRow.id = 'groupbuilder-item-' + data['groupTroveItemId'];
    logDebug('id set to: ' + newRow.id);
    for (var col = 0; col < newRow.childNodes.length; col++)
    {
        logDebug("working on item " + col);
        //Pull the id tag of this child
        var child = newRow.childNodes[col];
        if(child.nodeType == 1)
        {
            logDebug("Working on an element node: " + child.nodeName);
            var idstr = getNodeAttribute(child, 'id');
            child.id = null;
            var parsed = idstr.split(' ');
            if(parsed[1] == 'delete'){
                logDebug("createTroveRow 'delete'");
                //Replace the TROVEID string with the returned value
                var a = child.getElementsByTagName('a');
                var link = a[0].href;
                a[0].href = link.replace(/TROVEID/, data['groupTroveItemId']);
            }
            else if(parsed[1] == 'group') {
                logDebug("createTroveRow 'group'");
                if (data['name'].indexOf('group-') != 0) {
                    replaceChildNodes(child, null);
                }
            }
            else if(parsed[1] == 'versionLock') {
                logDebug("createTroveRow 'versionLock'");
                if (! data['versionLock']) {
                    var img = child.getElementsByTagName('img');
                    src = img[0].src;
                    img[0].src = src.replace(/locked/, 'unlocked');
                }
            }
            else if(parsed[1] == 'name') {
                logDebug("createTroveRow 'name'");
                replaceChildNodes(child, A({'href': data['referer'],
                                            'title': 'Name: ' + data['name'] + '; Version: ' +
                                            data['version']}, data['name']));
                logDebug("name finished");
            }
            else if(parsed[1] == 'projectName') {
                logDebug("createTroveRow 'projectName'");
                if(data[parsed[1]])
                    replaceChildNodes(child, A({'href': this.baseUrl + 'project/' + data[parsed[1]]}, data[parsed[1]]));
                else
                    replaceChildNodes(child, 'current');
            }
            else {
                logDebug("createTroveRow 'other'");
                log(data[parsed[1]]);
                replaceChildNodes(child, data[parsed[1]]);
            }
        }
        else{
            //Skip non element nodes
            logDebug("skipping non-element node");
        }
    }
    logDebug("Appending new row" + toHTML(newRow));
    this.tableNode.appendChild(newRow);
}

GroupTroveManager.prototype.troveAdded = function(items, data) {
    logDebug("troveAdded");
    var nodes = items.getElementsByTagName('int');
    data['groupTroveItemId'] = scrapeText(nodes[0]);
    //Now create the table row
    logDebug('data: ' + data);
    this.createTroveRow(data);
}

GroupTroveManager.prototype.troveAddedByProject = function(items, data) {
    logDebug('troveAddedByProject');
    logDebug('data: ' + data);
    var array = items.getElementsByTagName('array')[0].getElementsByTagName('array')[0];
    var values = array.getElementsByTagName('value');
    data['groupTroveItemId'] = scrapeText(values[0]);
    data['version'] = scrapeText(values[2]);
    logDebug("data is now: " + data);
    this.createTroveRow(data);
}

GroupTroveManager.prototype.troveDeleted = function(items) {
    logDebug("Trove deleted.  Data returned: " + items);
    var nodes = items.getElementsByTagName('int')
    var retVal = scrapeText(nodes[0]);
    //find the table row in question and remove it.
    swapDOM('groupbuilder-item-' + retVal, null);
}

function LinkManager()
{
    bindMethods(this);
}

LinkManager.prototype.setUrl = function(url) {
    this.url = url;
}

LinkManager.prototype.getUrlData = function(link) {
    var ques = link.indexOf('?');
    var args = new Object();
    var argstr = link.substring(ques+1, link.length);
    arglist = argstr.split(/;|&/);
    for (var i=0; i < arglist.length; i++) {
        var key, value;
        var x = arglist[i].split('=');
        args[x[0]] = x[1];
    }
    if( args['versionLock'] )
        args['versionLock'] = true;
    else
        args['versionLock'] = false;

    if(args['version'] == undefined)
        args['version'] = '';
    return args;
}

LinkManager.prototype.reworkLinks = function () {
    anchors = getElementsByTagAndClassName("a", null);
    //Iterate through the anchors looking for the links to addGroupTrove and deleteGroupTrove
    for(var i=0; i < anchors.length; i++) {
        var anchor = anchors[i];
        var href = anchor.href;
        if (href.indexOf('deleteGroupTrove') >= 0) {
            //Replace this with a javascript command
            var args = this.getUrlData(href);
            anchor.href = "javascript:groupTroveManager.deleteTrove('" + this.url + "', " +
                args['id'] + ", " + args['troveId'] + ');';
        }
        else if (href.indexOf('addGroupTrove') >= 0) {
            //Replace this with a javascript command
            var args = this.getUrlData(href);
            if (args['version']) {
                anchor.href = "javascript:groupTroveManager.addTrove('" + this.url + "', " +
                    args['id'] + ", '" + args['trove'] + "', '" + args['version'] + "', " +
                    args['versionLock'] + ", '" + args['referer'] + "');";
            }
            else if(args['projectName']){
                anchor.href = "javascript:groupTroveManager.addTroveByProject('" + this.url + "', " +
                    args['id'] + ", '" + args['trove'] + "', '" + args['projectName'] + "', " +
                    args['versionLock'] + ", '" + args['referer'] + "');";
            }
        }
    }
}

groupTroveManager = null;
linkManager = null;

function initGroupTroveManager() {
    //createLoggingPane(true);
    groupTroveManager = new GroupTroveManager();
    groupTroveManager.baseUrl = BaseUrl;
}

function initLinkManager() {
    linkManager = new LinkManager();
    linkManager.url = BaseUrl + 'xmlrpc';
    linkManager.reworkLinks();
}
