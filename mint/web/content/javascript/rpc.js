/*

    rpc.js

    A small RPC library for handling both XML-RPC and JSON-RPC.

    Copyright (c) 2005-2007 rPath, Inc.

*/


// GenericRpcRequest --------------------------------------------------------

// ctor
function GenericRpcRequest(aUrl, aMethod) {
    this.method = aMethod;
    this.url = BaseUrl + aUrl;
}

// common instance varibles
GenericRpcRequest.prototype.contentType = null;
GenericRpcRequest.prototype.callback = null;
GenericRpcRequest.prototype.callbackData = null;
GenericRpcRequest.prototype.deferred = null;
GenericRpcRequest.prototype.errback = null;
GenericRpcRequest.prototype.finalizer = null;
GenericRpcRequest.prototype.marshalParams = null;

// given an auth string (e.g. pysid) set it in the request
GenericRpcRequest.prototype.setAuth = function(aAuth) {
    this.auth = aAuth;
};

// set a callback handler used to handle the response from XmlHttpRequest
GenericRpcRequest.prototype.setCallback = function(aCallback) {
    this.callback = aCallback;
};

// set a data object used to pass to the callback
GenericRpcRequest.prototype.setCallbackData = function(aCallbackData) {
    this.callbackData = aCallbackData;
};

// set an errback handler for handling an error from XmlHttpRequest
GenericRpcRequest.prototype.setErrback = function(aErrback) {
    this.errback = aErrback;
};

// set a call that gets run no matter what (e.g. a finalizer)
GenericRpcRequest.prototype.setFinalizer = function(aFinalizer) {
    this.finalizer = aFinalizer;
};

// generic send function
// first argument is boolean; determines if send is asynchronous or not
// second argument is an array of arguments to marshal
GenericRpcRequest.prototype.send = function(aIsAsync, aArgList) {

    // we can't operate without a valid marshalParams function
    if (!this.marshalParams) {
        logFatal("Cannot marshal parameters without a marshalParam function");
        // TODO: error thrown here
    }

    // marshal the parameters to this function
    var marshaledData = this.marshalParams(aArgList);

    // get an XMLHttpRequest object
    var req = getXMLHttpRequest();

    // set up the object: we're using POST
    req.open("POST", this.url, aIsAsync);

    // content type should be set if specified by the subclass
    if (this.contentType) {
        req.setRequestHeader("Content-type", this.contentType);
    }

    // set the X-Session-Id header if we have an auth string
    if (this.auth) {
        req.setRequestHeader("X-Session-Id", this.auth);
    }

    // fire the gun here
    if (aIsAsync) {
        this.deferred = sendXMLHttpRequest(req, marshaledData);

        // setup callbacks/errback functions (if specified)
        if (!this.callback) {
            logWarn("No callback set; this might not be what you wanted");
        }
        else {
            if (this.callbackData) {
                this.deferred.addCallback(this.callback, this.callbackData);
            } else {
                this.deferred.addCallback(this.callback);
            }
        }
        if (this.errback) {
            this.deferred.addErrback(this.errback);
        }
        if (this.finalizer) {
            this.deferred.addBoth(this.finalizer);
        }
    } else {
        req.send(marshaledData);
        // TODO: better error handling here, please
        if (this.callbackData) {
            this.callback(this.callbackData, req);
        } else {
            this.callback(req);
        }
    }
};

// XmlRpcRequest ------------------------------------------------------------

// ctor
function XmlRpcRequest(aUrl, aMethod) {
    this.method = aMethod;
    this.url = BaseUrl + aUrl;
}

// XmlRpcRequest inherits from GenericRpcRequest
XmlRpcRequest.prototype = new GenericRpcRequest(null, null);

// specific MIME Content-Type for XML-RPC
XmlRpcRequest.prototype.contentType = "text/xml";

// marshal a list of params to an XML-RPC call
XmlRpcRequest.prototype.marshalParams = function(aArgList) {

    var mStr = '<?xml version="1.0"?>';
    mStr += '<methodCall>';
    mStr += '    <methodName>' + this.method + '</methodName>';
    mStr += '    <params>';

    for(var i = 0; i < aArgList.length; i++) {
        p = aArgList[i];
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
    this.url = BaseUrl + aUrl;
    logDebug("json Request: ", this.url);
}

// JsonRpcRequest inherits from GenericRpcRequest
JsonRpcRequest.prototype = new GenericRpcRequest(null, null);

// specific MIME Content-Type for JsonRPC
JsonRpcRequest.prototype.contentType = "application/x-json";

// marshal a list of params to a JsonRPC call
JsonRpcRequest.prototype.marshalParams = function(aArgList) {

    var ary = new Array();

    ary[0] = this.method;
    ary[1] = aArgList;

    mStr = serializeJSON(ary);
    logDebug("[JSON] request: ", mStr);

    return mStr;

};

