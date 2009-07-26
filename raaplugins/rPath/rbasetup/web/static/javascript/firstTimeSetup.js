//
// Copyright (c) 2008-2009 rPath, Inc.
// All rights reserved
//

function retryFirstTimeSetup() {
    d = postRequest('/rbasetup/rBASetup/retryFirstTimeSetup',
                    null, null, reloadNoHistory, '', false);
}
function updateCurrentStep(message, completed, errors) {
    if (message != '') {
            $('status_message').innerHTML = message.split("\n").join("<br />") + "<br /><br />";
            showElement('status_message');
        }

    if (completed) {
        if (errors.length > 0) {
            errorText = '<p>rBuilder was unable to compete the setup process.  Because some setup errors can be temporary, click the Retry button to attempt to complete the setup process.</p><p>If the error persists, please check your Networking and Internet Proxy settings in the Configuration menu to the left.</p><p>If you would like to contact rPath for assistance using any of the following methods:</p><ul><li>web: <a href="https://issues.rpath.com">https://issues.rpath.com</a></li><li>phone: +1 919.851.3984</li><li>email: <a href="mailto: support@rpath.com">support@rpath.com</a></li></ul><p>Please note the step that experienced the error, as well as the additional information displayed above.  Also, please use Collect Diagnostic Information link to the left to collect and download debugging information, and attach this file when filing an issue via the web.</p><br />';

            $('status_message').innerHTML += errors.replace('Failed: A permanent failure has occurred:', '') + errorText;
            showElement('status_message');
            setNodeAttribute('status_message', 'class', 'errormessage');
            removeElementClass('retry_button', 'off');
            setNodeAttribute('retry_button', 'href', 'javascript:retryFirstTimeSetup()');
        }
        else {
            removeElementClass('continue_button', 'off');
            setNodeAttribute('continue_button', 'href', 'javascript:button_submit(document.page_form)');
        }
    }
}

function getUpdatedStatus() {

    function _callback(req) {
        var message = req['statusmsg'];
        var statusCode = req['status'];
        var completed;
        var errors = req['errors'];
        if (req['reload']) {
            reloadNoHistory();
        }
        if (statusCode == TASK_RUNNING ||
            statusCode == TASK_SCHEDULED ||
            statusCode == TASK_PENDING ||
            statusCode == TASK_PREVENTED) {
            callLater(2, getUpdatedStatus);
            completed = false;
        }
        else {
            if (statusCode != TASK_SUCCESS &&
                errors == '') {
                errors = 'Unknown Error occurred';
            }
            completed = true;
        }
        updateCurrentStep(message, completed, errors);
    }

    function _callbackErr() {
        callLater(2, getUpdatedStatus);
    }

    postRequest('getFirstTimeSetupStatus', null, null,
            _callback, _callbackErr, false);
}

// Neuter the postRequest's WORKING message box for these requests; it's
// glitchy and redundant
post.showWorking = function(req) { void(0); }

addLoadEvent(getUpdatedStatus);

