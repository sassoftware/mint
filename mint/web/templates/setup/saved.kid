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
        <title>${formatTitle('rBuilder Product Setup')}</title>
    </head>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h1>rBuilder Product Setup</h1>
                <p>Your new configuration has been saved.</p>
                <p><a href="restart">Restart Server</a></p>
            </div>
        </td>
        <td id="right" class="projects">
            <div class="pad">
            </div>
        </td>
    </body>
</html>
