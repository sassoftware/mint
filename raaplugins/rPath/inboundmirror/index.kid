<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
    <?python 
        from rPath.inboundmirror.repeatschedule import MirrorScheduleWidget
    ?>
    <!--
         Copyright (c) 2005-2007 rPath, Inc.
         All rights reserved
    -->
    <head>
        <title>Schedule Inbound Mirroring</title>
        <script type="text/javascript">
            function enableMirror() {
                showElement("update");
            }

            function disableMirror() {
                hideElement("update");
            }

            function init() {
                if ('${enabled}' == 'True') {
                    getElement('enable').checked = true;
                    enableMirror();
                }
                else {
                    getElement('disable').checked = true;
                    disableMirror();
                }
                hideElement('inProgress');
                checkMirror();

            }

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
            addLoadEvent(init);

        </script>
    </head>

    <body id="middle">
        <h3>Schedule Inbound Mirroring</h3>
        <h5>Use this page to schedule syncing of local mirrors with their external
            repositories. To disable automated syncing, select "Disabled" below
            and click "Save." Local mirrors can be synced at any time by clicking "Mirror Now."</h5>
        <h5>NOTE: Mirrors are updated between the hour selected 
            and the following hour. The precise time a mirroring operation 
            will occur will be shown in a message dialog when the schedule
            is saved.</h5>
        <p style="margin-bottom: 0px;">Inbound mirroring is:</p>
        <form method="post" action="javascript:void(0);" onsubmit="javascript:postFormWizardRedirectOnSuccess(this, 'prefsSave');">
        <input type="radio" id="enable" name="status" value="enabled" onclick="enableMirror();"/>Enabled
        <input type="radio" id="disable" name="status" value="disabled" onclick="disableMirror();"/>Disabled
        <br/>
        <div id="update" style="padding-bottom: 0px;">
        <table style="border: 1px solid  #DDDDDD; margin-top: 10px; margin-bottom: 10px;">
            <tbody>
                <tr>
                    <td>Mirrrors will update:</td>  
                    <td>${MirrorScheduleWidget().display(dict(checkFreq=checkFreq, timeHour=timeHour, timeDay=timeDay, timeDayMonth=timeDayMonth, hours=hours))}</td>
                </tr>
            </tbody>
        </table>
        </div>
             <button type="submit" class="img"><img src="${tg.url('/static/images/save_button.png')}" alt="save" /></button>
        </form>
        <div style="border-top: 1px solid gray; clear: right; padding-top: 10px;"/>
        <div id="updateNow"> 
        <span style="float: left; font-style: italic; width: 60%">To update your local mirrors immediately, click "Mirror Now."</span>
        <button class="img" onclick="startMirrorNow();"><img src="${tg.url('/inboundmirror/static/images/mirror_now.png')}"/></button>
        </div>
        <div style="padding-top: 5px; font-style: italic;" id="inProgress">
            <span style="float: left;">Local mirrors are currently being updated...</span> 
            <img style="float: right;" src="${tg.url('/static/images/circle-ball-dark-antialiased.gif')}" />
        </div>
    </body>
</html>
