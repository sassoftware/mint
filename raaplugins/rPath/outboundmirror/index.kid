<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
    <?python 
        from raa.templates.repeatschedulewidget import RepeatScheduleWidget
    ?>
    <!--
         Copyright (c) 2005-2008 rPath, Inc.
         All rights reserved
    -->
    <head>
        <title>Schedule Outbound Mirroring</title>
        <script type="text/javascript">
            var timer;

            function checkMirror() {
                var p = new Post('checkMirrorStatus');
                var d = p.doAction();
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

            addLoadEvent(checkMirror);
        </script>
    </head>

    <body>
        <div class="plugin-page">

        <div class="page-section">
        Outbound Mirroring Schedule
        </div>
        <form name="page_form" action="javascript:void(0)" method="POST" onsubmit="javascript:postFormWizardRedirectOnSuccess(this, 'prefsSave');">
        <div class="page-section-content">
        Use this page to schedule mirroring of local repositories to Update Service appliance(s). To disable automated mirroring, select "No" below and click "Save."
        <p></p>
        NOTE: Update Service appliance(s) are updated between the hour selected and the following hour. The precise time a mirroring operation will occur will be shown in a message dialog when the schedule is saved.
        <p></p>
          ${RepeatScheduleWidget(schedule, enabled, toggleText='Enable inbound mirroring schedule?', toggleName='enabled', divClass='form-line')}
        <a class="rnd_button float-left" id="Save" href="javascript:button_submit(document.page_form)">Save</a>
        </div>
        </form>

        <div class="page-section">
        Mirror Now
        </div>

        <div id="updateNow">
            <div class="page-section-content">
            Click "Mirror Now" to start an outbound mirror immediately.
            <div class="button-line">
                <a class="rnd_button internal float-left" id="mirrorNowButton" onclick="javascript:startMirrorNow();">Mirror Now</a>
            </div>
            </div>
        </div>

        <div id="inProgress">
            <div class="page-section-content">
            <span style="float: left;">Local mirrors are currently being updated...</span>
            <img style="float: right;" src="${raa.web.makeUrl('/static/images/circle-ball-dark-antialiased.gif')}" />
            <br style="clear: right;" />
            <p>If you wish to monitor the status of the mirror operation,
               <a href="${raa.web.makeUrl('/logs/Logs')}">click here</a> and select
               "Outbound Mirroring" from the list of logs.
            </p>
            </div>
        </div>

        </div>
    </body>
</html>
