<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<?python
if 'traceback' not in locals():
    traceback = None
?>

<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Error')}</title>
    </head>
    <body>
        <div id="layout">
            <h2>Error:</h2>
            <p class="errormessage">${error}</p>
            <p>
                Please go back and try again or contact
                ${XML(cfg.supportContactHTML)}
                for assistance.
            </p>
            <div py:if="traceback" py:strip="True">
                <h2>Traceback:</h2>
                <pre py:content="traceback" />
            </div>
        </div>
    </body>
</html>
