var BaseUrl = "/tarrpc";
var curDisc = 0;
var needsDisc = 1;
var countDiscs = 0;
var serverName = "";

// Normalize a web path by prepending a / if missing, and appending
// a / if missing
function normPath(path) {
    if(path == "")
        path = "/";
    else if(path[path.length-1] != "/")
        path += "/";

    if(path[0] != "/")
        path = "/" + path;

    path = path.replace("//", "/");
    return path;
}

function readConcatStatus(aReq) {
    r = evalJSONRequest(aReq);
    percent = ((r.bytesRead / r.bytesTotal) * 100).toFixed(0);
    replaceChildNodes($('statusMessage'), "Concatenating: " + percent + "%");

    if(!r.done) {
        setTimeout("getConcatStatus()", 100);
    } else {
        alert("done concatting");
    }
}

function getConcatStatus() {
    var req = new JsonRpcRequest("/", "copyStatus");
    req.setCallback(readConcatStatus);
    req.send(true, []);
}

function startConcat() {
    var req = new JsonRpcRequest("/", "concatfiles");
    req.setCallback(getConcatStatus);
    req.send(true, []);
}

function readStatusCallback(aReq) {
    r = evalJSONRequest(aReq);
    percent = ((r.bytesRead / r.bytesTotal) * 100).toFixed(0);
    replaceChildNodes($('statusMessage'), "Copying: " + percent + "%");
    logDebug(percent);

    if(!r.done) {
        setTimeout("getCopyStatus()", 100);
    } else {
        if(curDisc < countDiscs) {
            needsDisc = curDisc + 1;
            replaceChildNodes($('statusMessage'), "Please insert disc " + needsDisc + " for " + serverName);
            $('goButton').removeAttribute('disabled');
            replaceChildNodes($('goButton'), "Continue");
        } else {
            alert("ready to untar");
            startConcat();
        }
    }
}

function getCopyStatus() {
    var req = new JsonRpcRequest("/", "copyStatus");
    req.setCallback(readStatusCallback);
    req.send(true, []);
}

function startCopy() {
    setNodeAttribute($('goButton'), 'disabled', true);
    var req = new JsonRpcRequest("/", "copyfiles");
    req.setCallback(getCopyStatus);
    req.send(true, []);
}

/* disc info retrieval */
function getDiscInfoCallback(aReq) {
    r = evalJSONRequest(aReq);

    logDebug("response from json: " + r);
    if(r.error) {
        var oldError = $('errorMessage');
        var el = DIV({ 'id': 'errorMessage' }, r.message);
        swapDOM(oldError, el);
    } else {
        if(r.curDisc != needsDisc || r.serverName != serverName) {
            replaceChildNodes($("statusMessage"), "Please insert disc " + needsDisc + " for " + serverName);
        } else {
            replaceChildNodes($("statusMessage"), "Mirror for " + r.serverName + ", disc " + r.curDisc + " of " + r.count + ".");
            curDisc = r.curDisc;
            countDiscs = r.count;
            startCopy();
        }
    }
}

function getDiscInfo(reqServerName) {
    serverName = reqServerName;
    var req = new JsonRpcRequest("/", "getDiscInfo");
    req.setCallback(getDiscInfoCallback);
    req.send(false, []);
}
