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

function readTarStatus(aReq) {
    r = evalJSONRequest(aReq);
    replaceChildNodes($('statusMessage'), "Untarred " + r.bytesRead + " files");

    if(!r.done && !r.error) {
        setTimeout("getTarStatus()", 250);
    } else if(r.error) {
        replaceChildNodes($('statusMessage'), r.errorMessage);
    } else {
        replaceChildNodes($('statusMessage'), "Done.");
        setElementClass($('statusMessage'), "finished");
        hideElement('goButton');
        showElement('finishLink');
    }
}

function getTarStatus() {
    var req = new JsonRpcRequest("/", "copyStatus");
    req.setCallback(readTarStatus);
    req.send(true, []);
}

function startUntar() {
    var req = new JsonRpcRequest("/", "untar");
    req.setCallback(getTarStatus);
    req.send(true, []);
}



function readConcatStatus(aReq) {
    r = evalJSONRequest(aReq);
    percent = ((r.bytesRead / r.bytesTotal) * 100).toFixed(0);
    replaceChildNodes($('statusMessage'), "Concatenating: " + percent + "%");

    if(!r.done) {
        setTimeout("getConcatStatus()", 250);
    } else {
        startUntar();
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

    if(percent == "100") {
        replaceChildNodes($('statusMessage'), "Verifying checksum...");
    } else {
        replaceChildNodes($('statusMessage'), "Copying: " + percent + "%");
    }

    if(!r.done) {
        setTimeout("getCopyStatus()", 250);
    } else if(r.checksumError) {
        replaceChildNodes($('statusMessage'), "Checksum error reading disc " + curDisc + ". Please contact your vendor for replacement.");
        setElementClass($('statusMessage'), 'error');
    } else {
        if(curDisc < countDiscs) {
            needsDisc = curDisc + 1;
            replaceChildNodes($('statusMessage'), "Please insert disc " + needsDisc + " for " + serverName);
            $('goButton').removeAttribute('disabled');
            replaceChildNodes($('goButton'), "Continue");
        } else {
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

    setElementClass($("statusMessage"), "running");

    logDebug("response from json: " + r);
    if(r.error) {
        replaceChildNodes($("statusMessage"), r.message);
        setElementClass($("statusMessage"), "error");
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
