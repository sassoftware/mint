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
// Some frequently used strings
var LockedVersionTitle = "Click to use the most recent version";
var UnlockedVersionTitle = "Click to lock version";

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

GroupTroveManager.prototype.toggleLockState = function (url, id) {
    //Figure out what to do first
    img = getElement('groupbuilder-item-lockicon-' + id);
    var lock = true;
    if(img.src.indexOf('unlocked') >= 0) {
        lock = false;
    }
    log("Current lock state: " + lock);
    logDebug('creating toggleLockState XMLRPC request object');
    var req = new XmlRpcRequest(url, 'setGroupTroveItemVersionLock');
    req.setAuth(getCookieValue('pysid'));
    req.setCallback(this.toggleVersionLock);
    req.setCallbackData({'id': id});
    logDebug("Sending the request");
    req.send(true, [id, Boolean(!lock)]);
}

GroupTroveManager.prototype.addTrove = function (url, id, name, version, versionLock, referer) {
    /* Form up the xmlrpc call and add this trove.
    */
    logDebug('Creating the addTrove xmlrpc request object');
    var req = new XmlRpcRequest(url, 'addGroupTroveItem');
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(this.troveAdded);
    req.setCallbackData({'id': id, 'name': name, 'version': version, 'versionLock': versionLock, 'referer': referer});
    logDebug("Sending the request");
    req.send(true, [id, name, version, '', '', Boolean(versionLock), false, false]);
}

GroupTroveManager.prototype.addTroveByProject = function (url, id, name, projectName, versionLock, referer) {
    /* Form up the xmlrpc call and add this trove.
    */
    logDebug('Creating the addTroveByProject xmlrpc request object');
    var req = new XmlRpcRequest(url, 'addGroupTroveItemByProject');
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(this.troveAddedByProject);
    req.setCallbackData({'id': id, 'name': name, 'projectName': projectName, 'versionLock': versionLock, 'referer': referer});
    logDebug("Sending the request");
    req.send(true, [id, name, projectName, '', '', Boolean(versionLock), false, false]);
}

GroupTroveManager.prototype.deleteTrove = function(url, id, troveId) {
    logDebug('Creating the deleteTrove xmlrpc request object');
    var req = new XmlRpcRequest(url, 'delGroupTroveItem');
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(this.troveDeleted);
    logDebug("Sending the request");
    req.send(true, [troveId]);
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
                var img = child.getElementsByTagName('img')[0];
                if (! data['versionLock']) {
                    var src = img.src;
                    img.src = src.replace(/locked/, 'unlocked');
                }
                img.id = img.id.replace(/TROVEID/, data['groupTroveItemId']);
                logDebug("Image ID: " + img.id);
                this.LinkManager.addLockLink(img);
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

GroupTroveManager.prototype.toggleVersionLock = function(data, req) {
    logDebug('toggleVersionLock');
    var xml = req.responseXML;
    var img = getElement('groupbuilder-item-lockicon-' + data['id']);
    var bools = xml.getElementsByTagName('boolean');
    var str = null;
    var title = null;
    locked = scrapeText(bools[1]) == '1'
    logDebug("returned state: " + locked);
    if(locked) {
        str = 'locked';
        title = LockedVersionTitle;
    }
    else{
        str = 'unlocked';
        title = UnlockedVersionTitle;
    }
    logDebug("current state as returned: " + str);
    img.src = img.src.replace(/unlocked|locked/, str);
    logDebug("Set src to: " + img.src);
    // Fix the tooltip
    img.title = title;
}

GroupTroveManager.prototype.troveAdded = function(data, req) {
    logDebug("troveAdded");
    var xml = req.responseXML;
    var nodes = xml.getElementsByTagName('int');
    data['groupTroveItemId'] = scrapeText(nodes[0]);
    //Now create the table row
    logDebug('data: ' + data);
    this.createTroveRow(data);
}

GroupTroveManager.prototype.troveAddedByProject = function(data, req) {
    logDebug('troveAddedByProject');
    var xml = req.responseXML;
    var array = xml.getElementsByTagName('array')[0].getElementsByTagName('array')[0];
    var values = array.getElementsByTagName('value');
    data['groupTroveItemId'] = scrapeText(values[0]);
    data['version'] = scrapeText(values[2]);
    logDebug("data is now: " + data);
    this.createTroveRow(data);
}

GroupTroveManager.prototype.troveDeleted = function(req) {
    logDebug("Trove deleted.  Data returned: " + req.responseText);
    var xml = req.responseXML;
    var nodes = xml.getElementsByTagName('int')
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

LinkManager.prototype.addLockLink = function (img) {
    logDebug('working with ' + img.id);
    var parts = img.id.split('-');
    var id = parts[parts.length-1];
    if(id != 'TROVEID'){
        var title = LockedVersionTitle;
        if(img.src.indexOf('unlocked') >= 0) {
            title = UnlockedVersionTitle;
        }
        img.title = title;
        var newimg = A({'href': 'javascript: groupTroveManager.toggleLockState("' +
                                this.url + '", ' + id + ');'
                       },
                       img.cloneNode(true));
        log("Swapping in " + toHTML(newimg));
        swapDOM(img, newimg);
    }
}

LinkManager.prototype.setupLockLinks = function () {
    logDebug("setupLockLinks");
    images = getElementsByTagAndClassName('img', 'lockicon');
    for(var i=0; i < images.length; i++) {
        this.addLockLink(images[i]);
    }
    logDebug('finished');
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
    groupTroveManager.LinkManager = linkManager;
}

function initLinkManager() {
    linkManager = new LinkManager();
    linkManager.url = 'xmlrpc/';
    linkManager.reworkLinks();
    linkManager.setupLockLinks();
}
