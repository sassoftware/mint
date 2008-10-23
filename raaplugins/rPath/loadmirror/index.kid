<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python 
import raa.templates.master 
import raa.web
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
    <!--
         Copyright (c) 2005-2007 rPath, Inc.
         All rights reserved
    -->
    <head>
        <title>Mirror Pre-load</title>
        <script type="text/javascript" src="${raa.web.makeUrl('/static/javascript/raa.js?v=14')}"></script>

        <script type="text/javascript">
            var schedId = ${schedId};

            function onWritePreloads(req) {
                if(req.done) {
                    projList = UL();
                    var candidates = req.projects.length;

                    for(var i in req.projects) {
                        project = req.projects[i][0];
                        hostname = req.projects[i][1];

                        if(req.preloadErrors[hostname]) {
                            error = req.preloadErrors[hostname];
                            appendChildNodes(projList, LI({}, project, SPAN({'style': 'color: red;'}, error)));
                            candidates--;
                        } else {
                            appendChildNodes(projList, LI({}, project, " - ", SPAN({'style': 'color: green;'}, "OK")));
                        }
                    }
                    swapDOM($('preloadProjects'), projList);
                    replaceChildNodes($('preloadCount'), "Projects eligible for mirror pre-loading: " + candidates);
                    getElement('preloadPrompt').style.display = ''; 

                    if(candidates > 0)
                        showElement($('startButton'));
                } else {
                    setTimeout(function () {getPreloads();}, 500);
                }
            }

            addLoadEvent(function() {
                refreshLog();
                getPreloads();
            });

            function getPreloads() {
                d = postRequest("callGetPreloads", ['schedId'], [schedId]);
                d = d.addCallback(callbackCheckError);
                d = d.addCallback(onWritePreloads);
                d = d.addErrback(callbackErrorGeneric);
            }

            function onRefreshLog(req) {
                logText = req.log;

                ta = TEXTAREA({'id': 'preloadLog', 'rows': '15', 'cols': '90'}, logText);
                swapDOM($('preloadLog'), ta);
                scrollToBottom('preloadLog');
                setTimeout("refreshLog()", 10000);
            }

            function refreshLog() {
                d = postRequest("callGetLog");
                d = d.addCallback(callbackCheckError);
                d = d.addCallback(onRefreshLog);
                d = d.addErrback(callbackErrorGeneric);
            }

            function startPreload() {
                d = postRequest("callStartPreload");
                hideElement($('startButton'));
            }

            // scroll to the bottom of a textarea
            function scrollToBottom(elName) {
                el = $(elName);
                el.scrollTop = el.scrollHeight;
            }
        </script>
    </head>

    <body>
        <div class="plugin-page">
        <div class="page-content">

 
        <div class="page-section">
        Mirror Pre-Load:
        </div>
        <div class="page-section-content">
            <div id="preloadPrompt" style="display: ${inProgress and 'none' or ''}">The mirror pre-load process will convert the following external projects into mirrored repositories:</div>
           <div id="preloadProjects">
                <div py:strip="True" py:if="inProgress">
                    A pre-loading operation is in progress.  Please see the activity log for details.
                </div>
                <div py:strip="True" py:if="not inProgress">
                    Please wait while the list of projects available to pre-load is retrieved...
                </div>
            </div>
            <div id="preloadCount"></div>
            <a class="rnd_button internal float-left" style="display: none;" id="startButton" onclick="javascript:startPreload();">Start Preloading</a>
        </div>

        <div class="page-section">
        Pre-load activity log:
        </div>
        <div class="page-section-content-bottom">
            <div id="logArea">
                <textarea rows="15" cols="90" id="preloadLog"></textarea>
                <p></p>
                <form name="page_form" action="downloadLog" method="GET">
                    <a class="rnd_button internal float-left" id="downloadLog" href="javascript:button_submit(document.page_form);">Download Log</a>
                </form>
            </div>
        </div>

        </div>
        </div>
    </body>
</html>
