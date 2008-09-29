<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
<?python
    from mint.web.templatesupport import projectText
?>

    <head>
        <title>${formatTitle('External %ss'%projectText().title())}</title>
    </head>
    <body>
        <div class="admin-page">
            <div id="left" class="side">
                ${adminResourcesMenu()}
            </div>
            <div id="admin-spanright">
                <div class="page-title-no-project">Externally-Managed ${projectText().title()}s</div>
                <p class="help">Externally-managed ${projectText().lower()}s allow a remote Conary repository to be accessible by
                        this rBuilder. Click on the name of an external ${projectText().lower()} to edit its settings.</p>
                <table class="results">
                    ${columnTitles(regColumns)}
                    ${searchResults(regRows)}
                </table>
    
                <h2>Mirrored ${projectText().title()}s</h2>
                <table class="results">
                    ${columnTitles(mirrorColumns)}
                    ${searchResults(mirrorRows)}
                </table>
                <br />
                <p class="p-button"><a href="addExternal"><b>Add a New External ${projectText().title()}</b></a></p>
                <br />
            </div>
            <div class="bottom"/>
        </div>
    </body>
</html>
