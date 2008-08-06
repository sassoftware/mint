<?xml version='1.0' encoding='UTF-8'?>
<?python
message = locals().get('message', None)
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid', 'packagecreator.kid', 'wizard.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Create Package: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
      <div id="layout">
        <div id="left" class="side">
            ${wizard_navigation()}
        </div>
        <div id="right" class="side">
            ${resourcePane()}
        </div>
        <div id="middle">
        <p py:if="message" class="message" py:content="message"/>
        <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
        <h2>Appliance Creator - Confirm Package Details</h2>
        ${createPackageInterview(editing, sessionHandle, factories, prevChoices)}
        </div>
      </div>
    </body>
</html>
