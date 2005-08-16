<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Error')}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
                <p class="error">Error:</p>
                
                <p class="errormessage">${error}</p>
                <p>
                    Please go back and try again or contact 
                    ${XML(cfg.supportContactHTML)}
                    for assistance.
                </p>
            </div>
        </td>
    </body>
</html>
