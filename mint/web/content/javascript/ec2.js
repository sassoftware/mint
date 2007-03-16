var statusId = 'startButton';
var spinnerImg = 'apps/mint/images/circle-ball-dark-antialiased.gif';


// ctor
function LaunchedAMI(launchedAMIId) {
    this.launchedAMIId = launchedAMIId;
    this.state = null;
    this.dns_name = null;
    bindMethods(this);
    this.updateStatus();
}

// attributes
LaunchedAMI.prototype.launchedAMIId = null;
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
        } else {
            var oldStatus = $(statusId);
            var newStatus = P(null, "Running on host " + this.dns_name);
            swapDOM(oldStatus, newStatus);
        }

    };

    var req = new JsonRpcRequest("jsonrpc/",
        "getLaunchedAMIInstanceStatus");
    req.setCallback(bind(callback, this));
    req.send(false, [this.launchedAMIId]);

};

// ctor
function EC2Launcher(blessedAMIId) {
    this.blessedAMIId = blessedAMIId;
    connect(statusId, "onclick", this, "launchAMI");
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
    req.setCallback(callback);
    req.send(true, [this.blessedAMIId]);

    // Update status button
    var oldStatus = $(statusId);
    var newStatus = P({'id':statusId}, IMG({'src': staticPath + spinnerImg}), "Launching...");
    disconnectAll(oldStatus);
    swapDOM(oldStatus, newStatus);

};

