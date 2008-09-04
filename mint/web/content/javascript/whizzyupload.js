/*
Copyright (C) 2008, rPath, Inc.
All Rights Reserved
*/

function getIframeDocument(node)
{
   var doc;
   // FF, etc ...
   if ( node.contentDocument )
   {
      doc = node.contentDocument;
   }
   // IE5.5 and later
   else if (node.contentWindow)
   {
      doc = node.contentWindow.document;
   }
   // IE5
   else if (node.document)
   {
      doc = node.document;
   }
   return doc;
}

function objectHasProperties(obj)
{
    var numProps = 0;
    for (var prop in obj)
    {
        if (true)
        {
            numProps += 1;
            break;
        }
    }
    return numProps !== 0;
}

function zeropad(num)
{
    if (num < 10)
    {
        return "0" + num;
    }
    return "" + num;
}

function format_eta(secs)
{
    var ret = "";
    if (secs > 3600)
    {
        ret += Math.round(secs/3600) + ":";
        secs = secs % 3600;
    }
    if (ret || secs > 60)
    {
        ret += zeropad(Math.round(secs/60)) + ":";
        secs = secs % 60;
    }
    if (ret)
    {
        ret += zeropad(secs);
    }
    else {
        ret += secs + " s";
    }
    return ret;
}

var FileUploadForm = function(upload_id, formkey, statusuri, canceluri)
{
    this.id=upload_id;
    this.form_key = formkey;
    this.status_uri = statusuri;
    this.cancel_uri = canceluri;

    // Polling interval
    this.upload_polling_rate = 1.5;
    this.numfiles = 0;

    bindMethods(this);
};

FileUploadForm.prototype =
{
    disableSubmit: function()
    {
        var d = $('submitButton_' + this.form_key);
        this.oldSubmitValue = d.value;
        d.disable = true;
        d.value='Please Wait...';
    },

    enableSubmit: function()
    {
        var d = $('submitButton_' + this.form_key);
        d.disable = false;
        d.value = this.oldSubmitValue;
    },

    displayUploadProgress: function()
    {
        this.disableSubmit();
        if (this.progressDialog !== null)
            this.progressDialog = jQuery("#upload_progress").dialog({
                modal: true,
                width: 475,
                height: 160,
                overlay: {
                    opacity: 0.5,
                    background: "black"
                }
            });
        else {
            this.progressDialog.dialog('open');
        }
        //Attach the cancel handler
        this.cancel_event = connect('upload_progress_cancel_button',
                  "onclick", this, 'cancelUpload');
    },

    resetUploadForm: function()
    {
        logDebug("resetting page");
        this.reloadIframes(); //Reset any iframes

        this.finishUpload();
        this.set0();
    },

    cancelUploadRequestFinished: function(req)
    {
        logDebug("cancelUploadRequestFinished");
        callLater(2, this.resetUploadForm);
    },

    cancelUploadRequest: function()
    {
        var d = loadJSONDoc(this.cancel_uri, {'uploadDirectoryHandle': this.id, 'fieldnames': this.getFieldnames()});
        d.addCallback(cancelUploadRequestFinished);
    },

    cancelUpload: function()
    {
        this.cancelled = true;

        //Update the message
        this.hideStatistics();

        //Send the cancel request (this should clean up after it's finished)
        this.cancelUploadRequest();
    },

    finishUpload: function()
    {
        logDebug("Cleaning up the progress dialog");
        //Hide the progress dialog, and call the cancel method
        if (this.progressDialog !== null)
        {
            this.progressDialog.dialog('close');
        }
        // kill the cancel button event
        if (this.cancel_event)
        {
            disconnect(this.cancel_event);
        }
        this.enableSubmit();
    },

    showUploadFinished: function()
    {
        //hideStatistics has already been called
        if (this.cancel_event)
        {
            disconnect(this.cancel_event);
        }
    },

    set0: function()
    {
        logDebug("resetting progress bar to 0");
        var percent = 0;
        $('progress_indicator_bar').style.width= "" + percent + "%";
        $('upload_progress_percent_complete').innerHTML = "" + percent + "%";
        $('upload_progress_wait').innerHTML = 'Please Wait...';
        $('upload_progress_statistics').style.display='none';
        $('upload_progress_wait').style.display='block';
    },

    set0: function()
    {
        logDebug("resetting progress bar to 0");
        var percent = 0;
        $('progress_indicator_bar').style.width= "" + percent + "%";
        $('upload_progress_percent_complete').innerHTML = "" + percent + "%";
        $('upload_progress_wait').innerHTML = 'Please Wait...';
        $('upload_progress_statistics').style.display='none';
        $('upload_progress_wait').style.display='block';
    },

    set100: function()
    {
        logDebug("setting complete status");
        //Probably don't need this, but it'd be silly to stop at 99% because of a rounding error
        var percent = 100;
        $('progress_indicator_bar').style.width= "" + percent + "%";
        $('upload_progress_percent_complete').innerHTML = "" + percent + "%";
        $('upload_progress_wait').innerHTML = 'Upload complete, processing file...';
    },

    showStatistics: function(sTime, cTime, read, total)
    {
        if (total == undefined)
        {
            $('upload_progress_statistics').style.display='none';
            $('upload_progress_wait').style.display='block';
        }
        else
        {
            logDebug("Showing statistics");
            $('upload_progress_cancel_button').disabled=false;
            var percent = Math.round(100*read/total);
            $('progress_indicator_bar').style.width= "" + percent + "%";
            $('upload_progress_percent_complete').innerHTML = "" + percent + "%";
            var rate = read/(cTime-sTime);
            $('upload_progress_rate').innerHTML = ""  + Math.round(rate/1024) + " KB/s";
            $('upload_progress_bytes').innerHTML = "uploaded " + Math.round(read/1024) + " of " + Math.round(total/1024) + " KB";
            $('upload_progress_eta').innerHTML = format_eta(Math.ceil((total-read)/rate));
            $('upload_progress_statistics').style.display='block';
            $('upload_progress_wait').style.display='none';
        }
    },

    hideStatistics: function()
    {
        $('upload_progress_cancel_button').disabled=true;
        $('upload_progress_statistics').style.display='none';
        $('upload_progress_wait').style.display='block';
    },

    getIframes: function()
    {
        return getElementsByTagAndClassName('iframe', null, this.form_key);
    },

    getFieldnames: function()
    {
        return map(function(x){
                return x.id.replace('_iframe', '');
            }, this.getIframes());
    },

    reloadIframes: function()
    {
        logDebug("Reloading iframes");
        //Reload the iframes
        forEach(this.getIframes(), function(x){
            getIframeDocument(x).location.replace(x.src);
            //Reset the hidden elements
            $(x.id.replace('_iframe', '')).value = '';
            });
    },

    doNextUpload: function()
    {
        //Get a list of all the iframes
        var iframes = this.getIframes();

        function filterElem(element_id, elem)
        {
            return getNodeAttribute(elem, 'name') == element_id;
        }

        var k=0;
        for(k=0; k < iframes.length; k++)
        {
            element_id = iframes[k].id.replace('_iframe', '');
            var iframedoc = getIframeDocument(iframes[k]);
            logDebug('doNextUpload inspecting iframe ' + element_id);
            if ($(element_id).value != 'UPLOADED')
            {
                //Make sure there's data to submit
                var e = filter(partial(filterElem, element_id), getElementsByTagAndClassName('input', null, iframedoc))[0];
                if(e.value)
                {
                    this.numfiles++;
                    //setup the poller for element_id
                    this.uploadStatus(element_id);
                    //grab the form and submit it
                    logDebug("doNextUpload submitting " + element_id + "'s form");
                    iframedoc.forms[0].submit();
                    return false;
                }
            }
        }
        return true;
    },

    uploadStatusCallFinished: function(key, req)
    {
        if (! this.cancelled){
            if (req.starttime !== null)
            {
                this.showStatistics(req.starttime, req.currenttime, req.read, req.totalsize);
            }
            if ((req.finished !== null) && objectHasProperties(req.finished))
            {
                //We're done, clean up
                //Set the hidden value to "UPLOADED" to prevent it from being resubmitted
                logDebug("We're finished, hiding statistics");
                this.hideStatistics();
                this.set100();
                $(key).value = 'UPLOADED';
                this.uploadComplete();
            }
            else {
                callLater(this.upload_polling_rate, partial(this.uploadStatus, key));
            }
        }
    },

    uploadStatus: function(key)
    {
        if (! this.cancelled) // This catches the case where we're not in a callback
        {
            //Poll the upload uri for a status update, at the end, either schedule another poll, or trigger uploadsComplete
            logDebug("Checking for status on " + this.id);
            var d = loadJSONDoc(this.status_uri, {'uploadDirectoryHandle': this.id, 'fieldname': key});
            //Add error handling for resiliency
            //Check to see if it's done
            d.addCallback(partial(this.uploadStatusCallFinished, key));
        }
        else
        {
            logDebug("upload cancelled, not checking status");
        }
    },

    uploadComplete: function()
    {
        //This only deals with embedded iFrames, any other checks should be
        //done via overrides
        wedoneyet = this.doNextUpload();
        if (!wedoneyet)
        {
            return wedoneyet;
        }
        else
        {
            //TODO: add message updating progress
            logDebug("Finished uploading all subframes, submitting main form");
            $(this.form_key).submit();
            this.showUploadFinished();
            return true;
        }
    },

    submitFormData: function(form)
    {
        try {
            this.cancelled = false;
            //Display the upload dialog
            this.displayUploadProgress();

            //Check that we have data to upload
            if (! this.uploadComplete())
            {
                return false;
            }

            //We don't want to submit the form here
            return false;
        }
        catch (ex)
        {
            logDebug(ex);
            this.cancelUpload();
            return false;
        }
    }
};
