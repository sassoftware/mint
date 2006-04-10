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
        <title>${formatTitle('Maintenance')}</title>
    </head>
    <body>
        <div class="layout">
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            <div id="spanleft">
            <h2>Site is temporarily down</h2>
            <p class="errormessage">${cfg.productName} is currently undergoing maintenance.</p>
            <p>
                A posting will be made on
                <a href="${cfg.announceLink}">Site Announcements</a>
                when this situaion is resolved.
            </p>
            <p>
                contact
                ${XML(cfg.supportContactHTML)}
                for assistance.
            </p>
            </div>
        </div>
    </body>
</html>
