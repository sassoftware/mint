<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
    <!--
         Copyright (c) 2006 rPath, Inc.
         All rights reserved
    -->
    <head>
        <title>Mirror Pre-load</title>
        <script type="text/javascript" src="${tg.url('/static/javascript/raa.js?v=14')}"></script>

        <script type="text/javascript">
            var schedId = ${schedId};
            var logShown = false;

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
                setTimeout("refreshLog()", 2000);
            }

            function refreshLog() {
                d = postRequest("callGetLog");
                d = d.addCallback(callbackCheckError);
                d = d.addCallback(onRefreshLog);
                d = d.addErrback(callbackErrorGeneric);
            }

            function startPreload() {
                d = postRequest("callStartPreload");
            }

            function toggleShowLog() {
                if(logShown) {
                    hideElement($('logArea'));
                    replaceChildNodes($('showLogButton'), "Show Log");
                    logShown = false;
                } else {
                    showElement($('logArea'));
                    replaceChildNodes($('showLogButton'), "Hide Log");
                    logShown = true;
                }
                scrollToBottom('preloadLog');
            }

            // scroll to the bottom of a textarea
            function scrollToBottom(elName) {
                el = $(elName);
                el.scrollTop = el.scrollHeight;
            }
        </script>
    </head>

    <body id="middleWide">
        <div>
            <h3>Mirror Pre-Load:</h3>
            <p id="preloadPrompt">The mirror pre-load process will convert the following external projects into mirrored repositories:</p>
            <p id="preloadProjects">
                Please wait while the list of projects available to pre-load is retrieved...
            </p>
            <p id="preloadCount"></p>
            <button onclick="javascript:startPreload();" style="display: none;" id="startButton">Start Preloading</button>
            <hr />
            <button onclick="javascript:toggleShowLog();" id="showLogButton">Show Log</button>
            <div id="logArea" style="display: none;">
                <h4>Pre-load activity log:</h4>
                <textarea rows="15" cols="90" id="preloadLog"></textarea>
                <p><a href="downloadLog"><img src="${tg.url('/static/images/download_button.png')}" alt="Download" /></a></p>
            </div>
        </div>
    </body>
</html>
