<?xml version='1.0' encoding='UTF-8'?>
<?python
from conary.lib.cfg import *
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>rBuilder Configuration Complete</title>
    </head>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h1>rBuilder Configuration Complete</h1>

                <p>Your rBuilder server has now been configured.  Now it's
                time to launch rBuilder, and make it available to your
                users.</p>

                <p>To do so, click on the "Launch" button below.  After a
                short delay, you will be directed to the rBuilder front
                page, where you can login and create the project(s) your
                users require.</p>

                <div><img id="spinner" src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" /></div>
                <p>
                    <a href="restart" onclick="javascript:$('spinner').style.visibility = 'visible';">
                        <img src="${cfg.staticPath}apps/mint/images/launch_button.png" alt="Launch" />
                    </a>
                </p>
            </div>
        </td>
        <td id="right" class="projects">
            <div class="pad">
            </div>
        </td>
    </body>
</html>
