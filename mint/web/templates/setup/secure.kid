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
        <div class="layout">
            <h1>rBuilder Product Setup</h1>
            <p>Please run: <strong><tt>touch ${cfg.dataPath}${sid}.txt</tt></strong> on your rBuilder server to continue.</p>
            <p>This is to ensure that you, the user of this setup tool, has physical access to the machine hosting this application.</p>
            <p>When you have created that file, <strong><a href="${cfg.basePath}setup/">reload</a></strong>.</p>
        </div>
    </body>
</html>
