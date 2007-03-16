//
// Copyright (C) 2007 rPath, Inc
// All Rights Reserved
//

// ctor
function LaunchedAMI(launchedAMIId) {
    this.launchedAMIId = launchedAMIId;
    bindMethods(this);
    this.getLaunchedAMIData();
    this.updateStatus();
}

// attributes
LaunchedAMI.prototype.launchedAMIId = null;
LaunchedAMI.prototype.data = null;
LaunchedAMI.prototype.state = null;
LaunchedAMI.prototype.dns_name = null;

// status updater
LaunchedAMI.prototype.updateStatus = function() {

    // callback for launch status
    var callback = function(aReq) {
        logDebug("updateStatus response:", aReq.responseText);

        var req = evalJSONRequest(aReq);
        this.state = req[0];
        this.dns_name = req[1];

        if (this.state == 'pending') {
            callLater(5, this.updateStatus);
        }
        else {
            this.updatePageWithNewState();
        }
    };

    var req = new JsonRpcRequest("jsonrpc/",
        "getLaunchedAMIInstanceStatus");
    req.setCallback(bind(callback, this));
    req.send(true, [this.launchedAMIId]);

};

LaunchedAMI.prototype.updatePageWithNewState = function() {
    hideElement("div_during_launch");
    if (this.state == 'running') {
        setNodeAttribute('rapLink', 'href', "http://"+this.dns_name+":8004/");
        replaceChildNodes('rapPassword', this.data['raaPassword']);
        showElement("div_success");
    }
    else {
        showElement("div_failure");
    }
};

LaunchedAMI.prototype.getLaunchedAMIData = function() {

    // callback for launch status
    var callback = function(aReq) {
        logDebug("getLaunchedAMI response:", aReq.responseText);
        var req = evalJSONRequest(aReq);
        this.data = req;
    };

    var req = new JsonRpcRequest("jsonrpc/", "getLaunchedAMI");
    req.setCallback(bind(callback, this));
    req.send(false, [this.launchedAMIId]);

};

// ctor
function EC2Launcher(blessedAMIId) {
    this.blessedAMIId = blessedAMIId;
    connect("startButton", "onclick", this, "launchAMI");
    bindMethods(this);
}

// attributes
EC2Launcher.prototype.blessedAMIId = null;
EC2Launcher.prototype.launchedAMI = null;

// functions
EC2Launcher.prototype.launchAMI = function(e) {

    // callback for launch request
    var callback = function(aReq) {
        logDebug("launchAMI response:", aReq.responseText);
        req = evalJSONRequest(aReq);
        this.launchedAMI = new LaunchedAMI(req);
    };

    // request the backend to launch the AMI instance
    var req = new JsonRpcRequest("jsonrpc/",
        "launchAMIInstance");
    req.setCallback(bind(callback, this));
    req.send(true, [this.blessedAMIId]);

    // Update status button
    disconnectAll($('startButton'));
    hideElement('div_before_launch');
    showElement('div_during_launch');

};

