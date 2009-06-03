//
// Copyright (c) 2008-2009 rPath, Inc.
// All rights reserved
//

function retryFirstTimeSetup() {
    d = postRequest('/rbasetup/rBASetup/retryFirstTimeSetup',
                    null, null, reloadNoHistory, '', false);
}
function updateCurrentStep(stepNumber, completed, completedMsg) {
    var step = 'step' + stepNumber;
    var currentFound = false;

    var liEl = $('statusList');
    forEach (liEl.getElementsByTagName('li'), function (e) {
        if (e.id.indexOf(step) >= 0) {
            currentFound = true;
            if (completed) {
                if ( completedMsg.length > 0 ) {
                    setElementClass(e, 'failedState');
                }
                else {
                    setElementClass(e, 'completedState');
                }
            }
            else {
                setElementClass(e, 'currentState');
            }
        }
        else {
            if (!currentFound && stepNumber > 0)  {
                setElementClass(e, 'completedState');
            }
        }
    });

    if (completed) {
        var msg = completedMsg || '';
        if (msg.length > 0) {
            $('status_message').innerHTML = completedMsg;
            showElement('status_message');
            setNodeAttribute('status_message', 'class', 'errormessage')
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
        var newStep = req['currentStep'];
        var statusCode = req['status'];
        var completed;
        var errors;
        if (statusCode == TASK_RUNNING ||
            statusCode == TASK_SCHEDULED ||
            statusCode == TASK_PENDING ||
            statusCode == TASK_PREVENTED) {
            callLater(2, getUpdatedStatus);
            completed = false;
        }
        else {
            completed = true;
            if (statusCode != TASK_SUCCESS) {
                errors = req['statusmsg'];
            }
        }
        updateCurrentStep(newStep, completed, errors);
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

