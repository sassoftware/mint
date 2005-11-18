/* 
    Copyright (C) 2005 rpath, Inc.

    All Rights Reserved
*/

/* An XMLRPC client class.
   
   Example:

    function processRequest(xml) {
        // do something with the xml object here
    }

    var req = new XmlRpcRequest("/url/", "myMethod");
    req.setHandler(processRequest);
    req.send(arg1, arg2, ...);
*/

function XmlRpcRequest(url, method)
{
    var req = getXMLHttpRequest();
    var auth = null;
    var handler = null;
    var data = null;

    this.req = req;
    this.url = url;
    this.method = method;
    this.auth = auth;
    this.handler = handler;

    function setAuth(auth) {
        this.auth = auth;
    }

    function setHandler(myHandler, myData) {
        handler = myHandler;
        data = myData;
    }

    function stateChange() {
        if(req.readyState == 4) {
            if(req.status == 200) {
                if(handler) {
                    if(data){
                        handler(req.responseXML, data);
                    }
                    else {
                        handler(req.responseXML);
                    }
                }
            }
            else {
                // don't do this, because we could spam the user with dialog boxes.
                log("XMLRPC call returned " + req.status);
                // alert("There was a problem processing the XML data:\n" + req.statusText);
            }
        }
    }

    function send() {
        var msg = '<?xml version="1.0"?>';
        msg += '<methodCall>';
        msg += '    <methodName>' + method + '</methodName>';
        msg += '    <params>';

        for(var i = 0; i < arguments.length; i++) {
            p = arguments[i];
            t = typeof(arguments[i]);

            msg += '<param>';
            switch(t) {
                case "number":
                    msg += '<value><int>' + p + '</int></value>';
                    break;
                case "string":
                    msg += '<value><string>' + p + '</string></value>';
                    break;
                case "boolean":
                    msg += '<value><boolean>' + Number(p) + '</boolean></value>';
                    break;
                default:
                    alert("Unable to marshal " + t + " types");
            }
            msg += '</param>';
        }
        msg += '</params></methodCall>';

        this.req.onreadystatechange = stateChange;
        this.req.open("POST", this.url, true);
        this.req.setRequestHeader("Content-type", "text/xml");
        if(this.auth) {
            this.req.setRequestHeader("X-Session-Id", this.auth);
        }
        this.req.send(msg);
    }

    this.setAuth = setAuth;
    this.setHandler = setHandler;
    this.send = send;
    this.data = data;
}
