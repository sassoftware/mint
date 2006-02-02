/*

    rpc.js

    A small RPC library for handling both XML-RPC and JSON-RPC.

    Copyright (c) 2006 rPath, Inc.

*/


// GenericRpcRequest --------------------------------------------------------

// ctor
function GenericRpcRequest(aUrl, aMethod) {
    this.method = aMethod;
    this.url = aUrl;
}

// common instance varibles
GenericRpcRequest.prototype.contentType = null;
GenericRpcRequest.prototype.callback = null;
GenericRpcRequest.prototype.errback = null;
GenericRpcRequest.prototype.marshalParams = null;
GenericRpcRequest.prototype.deferred = null;

// given an auth string (e.g. pysid) set it in the request
GenericRpcRequest.prototype.setAuth = function(aAuth) {
    this.auth = aAuth;
};

// set a callback handler used to handle the response from XmlHttpRequest
GenericRpcRequest.prototype.setCallback = function(aCallback) {
    this.callback = aCallback;
};

// set an errback handler for handling an error from XmlHttpRequest
GenericRpcRequest.prototype.setErrback = function(aErrback) {
    this.errback = aErrback;
};

// generic send function
GenericRpcRequest.prototype.send = function() {

    // we can't operate without a valid marshalParams function
    if (!this.marshalParams) {
        logFatal("Cannot marshal parameters without a marshalParam function");
        // TODO: error thrown here
    }

    // marshal the parameters to this function
    marshaledData = this.marshalParams(arguments);

    // get an XMLHttpRequest object
    req = getXMLHttpRequest();

    // set up the object: we're using POST
    req.open("POST", this.url, true);

    // content type should be set if specified by the subclass
    if (this.contentType) {
        req.setRequestHeader("Content-type", this.contentType);
    }

    // set the X-Session-Id header if we have an auth string
    if (this.auth) {
        req.setRequestHeader("X-Session-Id", this.auth);
    }

    // fire the gun here
    this.deferred = sendXMLHttpRequest(req, marshaledData);

    // setup callbacks/errback functions (if specified)
    if (!this.callback) {
        logWarn("No callback set; this might not be what you wanted");
    }
    else {
        this.deferred.addCallback(this.callback);
    }

    if (this.errback) {
        this.deferred.addErrback(this.errback);
    }

};

// XmlRpcRequest ------------------------------------------------------------

// ctor
function XmlRpcRequest(aUrl, aMethod) {
    this.method = aMethod;
    this.url = aUrl;
}

// XmlRpcRequest inherits from GenericRpcRequest
XmlRpcRequest.prototype = new GenericRpcRequest(null, null);

// specific MIME Content-Type for XML-RPC
XmlRpcRequest.prototype.contentType = "text/xml";

// marshal a list of params to an XML-RPC call
XmlRpcRequest.prototype.marshalParams = function() {

    var paramList = arguments[0];

    var mStr = '<?xml version="1.0"?>';
    mStr += '<methodCall>';
    mStr += '    <methodName>' + this.method + '</methodName>';
    mStr += '    <params>';

    for(var i = 0; i < paramList.length; i++) {
        p = paramList[i];
        t = typeof(p);

        mStr += '<param>';
        switch(t) {
            case "number":
                mStr += '<value><int>' + p + '</int></value>';
                break;
            case "string":
                mStr += '<value><string>' + p + '</string></value>';
                break;
            case "boolean":
                mStr += '<value><boolean>' + Number(p) + '</boolean></value>';
                break;
            default:
                logWarn("Unable to marshal " + t + " types");
        }
        mStr += '</param>';
    }
    mStr += '</params></methodCall>';

    logDebug("[XML-RPC] request: ", mStr);

    return mStr;

};

// JsonRpcRequest -----------------------------------------------------------

// ctor
function JsonRpcRequest(aUrl, aMethod) {
    this.method = aMethod;
    this.url = aUrl;
}

// JsonRpcRequest inherits from GenericRpcRequest
JsonRpcRequest.prototype = new GenericRpcRequest(null, null);

// XmlRpcRequest inherits from GenericRpcRequest
JsonRpcRequest.prototype = new GenericRpcRequest(null, null);

// specific MIME Content-Type for XML-RPC
JsonRpcRequest.prototype.contentType = "application/x-json";

// marshal a list of params to an XML-RPC call
JsonRpcRequest.prototype.marshalParams = function() {

    var ary = new Array();

    ary[0] = this.method;
    ary[1] = arguments[0];

    mStr = serializeJSON(ary);

    logDebug("[JSON] request: ", mStr);

    return mStr;

};

