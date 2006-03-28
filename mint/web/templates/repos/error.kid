<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
 Copyright (c) 2005-2006 rPath, Inc.

 All Rights Reserved
-->
    <head>
        <title>${formatTitle('Repository Error')}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="middle">
                <h2>Error</h2>
                <pre class="error">${error}</pre>
                <p>Please go back and try again.</p>
            </div>
        </div>
    </body>
</html>
