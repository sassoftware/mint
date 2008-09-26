<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
    <?python 
        from raa.templates.repeatschedulewidget import RepeatScheduleWidget
        import raa.web
    ?>
    <!--
         Copyright (c) 2005-2008 rPath, Inc.
         All rights reserved
    -->
    <head>
        <title>Schedule Inbound Mirroring</title>
        <script type="text/javascript">
            var timer;

            function checkMirror() {
                var d = loadJSONDoc('checkMirrorStatus');
                d = d.addCallbacks(updateDisplay, callbackErrorGeneric);
            }

            function updateDisplay(req) {
                if (req.mirroring) {
                    hideElement('updateNow');
                    showElement('inProgress');
                }
                else {
                    hideElement('inProgress');
                    showElement('updateNow');
                }
                timer = setTimeout(checkMirror, 10000);
            }
                    
            function startMirrorNow() {
                hideElement('updateNow');
                showElement('inProgress');
                var d = loadJSONDoc('mirrorNow');
                clearTimeout(timer);
                d = d.addCallbacks(function () {setTimeout(checkMirror, 6000);},
                                   callbackErrorGeneric);
            }

            addLoadEvent(updateDisplay);
        </script>
    </head>

    <body>
        <div class="plugin-page">

        <div class="page-section">
        Inbound Mirroring Schedule
        </div>
        <form name="page_form" action="javascript:void(0)" method="POST" onsubmit="javascript:postFormWizardRedirectOnSuccess(this, 'savePrefs');">
        <div class="page-section-content">
        Use this page to schedule syncing of local mirrors with their external repositories. To disable automated syncing, select "No" below and click "Save."
        <p></p>
        NOTE: Mirrors are updated between the hour selected and the following hour. The precise time a mirroring operation will occur will be shown in a message dialog when the schedule is saved.
        <p></p>
          ${RepeatScheduleWidget(schedule, enabled, toggleText='Enable inbound mirroring schedule?', toggleName='enabled', divClass='form-line')}
        <a class="rnd_button float-left" id="Save" href="javascript:button_submit(document.page_form)">Save</a>
        </div>
        </form>


        <div class="page-section">
        Mirror Now
        </div>
        <div class="page-section-content">
        Click "Mirror Now" to start an inbound mirror immediately.
        <div id="updateNow"> 
            <div class="button-line">
                <a class="rnd_button internal float-left" id="mirrorNowButton" onclick="javascript:startMirrorNow();">Mirror Now</a>
            </div>
        </div>
        </div>

        <div style="padding-top: 5px; font-style: italic;" id="inProgress">
            <span style="float: left;">Local mirrors are currently being updated...</span>
            <img style="float: right;" src="${raa.web.makeUrl('/static/images/circle-ball-dark-antialiased.gif')}" />
            <br style="clear: right;" />
            <p>If you wish to monitor the status of the mirror operation,
               <a href="${raa.web.makeUrl('/logs/Logs')}">click here</a> and select
               "Inbound Mirroring" from the list of logs.
            </p>
        </div>

        </div>
    </body>
</html>
