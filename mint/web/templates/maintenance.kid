<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<?python
if 'traceback' not in locals():
    traceback = None
from mint import config
defaultConfig = config.MintConfig()
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
            <h2>Maintenance in Progress</h2>

            <p>${cfg.productName} is currently undergoing maintenance.
            During this time, you will be unable to access the site.</p>

            <p py:if="cfg.announceLink != defaultConfig.announceLink">Check the <a
            href="${cfg.announceLink}">site announcements</a> for current
            status.</p>

            <p py:if="cfg.supportContactHTML != defaultConfig.supportContactHTML">Contact
            ${XML(cfg.supportContactHTML)} if you have any questions.</p>

            <p>${cfg.productName} administrators: To access
            maintenance-mode functions, enter your username and
            password to login.</p>
            </div>
        </div>
    </body>
</html>
