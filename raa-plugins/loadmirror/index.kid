<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
<!--    
     Copyright (c) 2005-2006 rPath, Inc.
     All rights reserved
-->    


<head>
    <title>Mirror Pre-load</title>
    <script type="text/javascript" src="${tg.url('/static/javascript/raa.js?v=14')}"></script>

    <script type="text/javascript">
        function writePreloads(req) {
            projList = UL();
            logDebug(req.projects);
            logDebug(req.preloadErrors);
            var candidates = req.projects.length;

            for(var i in req.projects) {
                logDebug(i);
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
        }

        addLoadEvent(function() {
            d = postRequest("callGetPreloads");
            d = d.addCallback(callbackCheckError);
            d = d.addCallback(writePreloads);
            d = d.addErrback(callbackErrorGeneric);
        });
    </script>
</head>

<body id="middleWide">
    <div>
        <h3>Mirror Pre-Load:</h3>
        <p id="preloadPrompt">The mirror pre-load process will convert the following external projects into mirrored repositories:</p>
        <p id="preloadProjects">
            Please wait while the list of projects available to preload is retrieved...
        </p>
        <p id="preloadCount"></p>
    </div>
</body>
</html>
