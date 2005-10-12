function add(targetId, sourceId) {
    target = document.getElementById(targetId);
    source = document.getElementById(sourceId);

    var source_len = source.length;
    var target_len = target.length;

    for (var i=0; i < source_len; i++) {
    
        opt = source.options[i];
        if (opt.selected == true && opt.value != "") {
            if (opt.style.fontWeight == "bold")
                return;

            opt.style.fontWeight = "bold";

            target.options[target_len] = new Option(opt.text, opt.value);
            target_len ++;
        }
    }
}

function toggle_display(tid) {
    if(document.getElementById(tid).style.display == "none") {
        document.getElementById(tid).style.display = "";
        img = document.getElementById(tid + "_expander");
        img.src = img.src.replace('expand', 'collapse')
    }
    else {
        document.getElementById(tid).style.display = "none";
        img = document.getElementById(tid + "_expander");
        img.src = img.src.replace('collapse', 'expand')
    }
}

function remove(targetId, sourceId) {
    target = document.getElementById(targetId);
    source = document.getElementById(sourceId);

    var source_len = source.length;
    var target_len = target.length;

    for (var i = target_len-1; i >= 0; i--) {
        opt = target.options[i];

        if (opt.selected == true) {
            target.options[i] = null;
            target_len--;           
 
            for (var j=0; j < source_len; j++) {
                sopt = source.options[j];
                if (opt.value == sopt.value) {
                    sopt.style.fontWeight = "normal";
                }
            }
        }
    }
}

function select_all(selId) {
  sel = document.getElementById(selId);
  for (i=0; i < sel.length; i++) {
    sel.options[i].selected = true;
  }
}

// check all checkboxes of name 'name'
// if self.checked, and vice-versa
function mark_all(selfId, id, name) {
    self = document.getElementById(selfId);
    items = document.getElementsByName(name);

    for(var i = 0; i < items.length; i++) {
        item = items[i];
        if(item.id == id) {
            item.checked = self.checked;
        }
    }
}

// check or uncheck all checkboxes of name 'name'
function check_all(name, checked) {
    items = document.getElementsByName(name);

    for(var i = 0; i < items.length; i++) {
        items[i].checked = checked;
    }
}

// appends a new item to a select element 
function appendToSelect(select, value, content, className) {
    var o = document.createElement("option");
    o.value = value;
    o.className = className;
    o.appendChild(content);
    select.appendChild(o);
}

// clears the contents of a selectelement
function clearSelection(select) {
    while (select.length > 0) {
        select.remove(0);
    }
}

// returns the value of a named cookie
function getCookieValue (cookie) {
    var e= new RegExp(escape(cookie) + "=([^;]+)");
    if(e.test(document.cookie + ";")) {
        e.exec(document.cookie + ";");
        return unescape(RegExp.$1);
    }
    else
        return false;
}

var STATUS_WAITING = 0;
var STATUS_RUNNING = 1;
var STATUS_FINISHED = 2;
var STATUS_DELETED = 3;
var STATUS_ERROR = 4;
var STATUS_NOJOB = 5;
var refreshed = false;

function processGetReleaseStatus(xml) {
    el = document.getElementById("jobStatus");
    var status = xml.getElementsByTagName("int")[0].firstChild.data;
    var statusText = xml.getElementsByTagName("string")[0];
    if(!statusText.firstChild) {
        statusText = "No status";
        status = STATUS_NOJOB;
    } else {
        statusText = statusText.firstChild.nodeValue;
    }
    el.replaceChild(document.createTextNode(statusText), el.firstChild);
    
    downloads = document.getElementById("downloads");
    editOptions = document.getElementById("editOptions");
    editOptionsDisabled = document.getElementById("editOptionsDisabled");

    if(status > STATUS_RUNNING) {
        editOptionsDisabled.style.display = "none";
        editOptions.style.display = "block";
        downloads.style.visibility = "visible";
    } else {
        editOptionsDisabled.style.display = "block";
        editOptions.style.display = "none";
        downloads.style.visibility = "hidden";
    }
}

function processGetTroveList(xml) {
    sel = document.getElementById("trove");

    clearSelection(sel);
    var response = xml.getElementsByTagName("struct")[0];

    var members = response.getElementsByTagName("member");
    for(var i = 0; i < members.length; i++) {
        var nameNode = members[i].getElementsByTagName("name")[0];
        var label = nameNode.firstChild.nodeValue;
        // appendToSelect(sel, label, document.createTextNode(label), "label");

        var troves = members[i].getElementsByTagName("string");
        for(var j = 0; j < troves.length; j++) {
            var troveName = troves[j].firstChild.nodeValue;
            appendToSelect(sel, troveName + "=" + label, document.createTextNode(troveName), "trove");
        }
    }
    document.getElementById("submitButton").disabled = false;
}

function getReleaseStatus(releaseId) {
    var req = new XmlRpcRequest("/xmlrpc", "getReleaseStatus");
    req.setAuth(getCookieValue("pysid"));
    req.setHandler(processGetReleaseStatus);
    req.send(releaseId);

    // restart the timeout to refresh every 1 seconds
    setTimeout("getReleaseStatus(" + releaseId + ")", 5000);
}

function getTroveList(projectId) {
    var req = new XmlRpcRequest("/xmlrpc", "getGroupTroves");
    req.setAuth(getCookieValue("pysid"));
    req.setHandler(processGetTroveList);
    req.send(projectId);

    setTimeout("ticker()", 200);
}

var ticks = 0;
var direction = 1;

function ticker() {
    el = document.getElementById("pleaseWait");

    if(el) {
        if(direction == 1)
        {
            el.text += ".";
            ticks++;

            if(ticks >= 3)
                direction = -1;
        } else {
            el.text = el.text.substring(0, el.text.length-1);
            ticks--;
            if(ticks == 0)
                direction = 1;
        }
        setTimeout("ticker()", 200);
    }
}
