<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../library.kid'">
<!--
 Copyright (c) 2005 rPath, Inc.

 All Rights Reserved
-->
    <head>
        <title>${formatTitle('Repository Error')}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()} 
                ${browseMenu(display='none')}
                ${searchMenu(display='none')}
            </div>
        </td>
        <td id="main">
          <div id="content">
            <h2>Error</h2>
            <pre class="error">${error}</pre>
            <p>Please go back and try again.</p>
          </div>
        </td>
    </body>
</html>
