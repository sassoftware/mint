<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Administer')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <h2>${cfg.productName} Administration</h2>

            <p>This is the main ${cfg.productName} administration page. Using
                the menu to the left, you can:</p>

                <ul>
                    <li>View currently-running and recently-completed jobs</li>
                    <li>View ${cfg.productName} usage reports</li>
                    <li>Create ${cfg.productName} user accounts</li>
                    <li>Send email to all registered ${cfg.productName} users</li>
                    <li>Add projects that reference remote repositories</li>
                    <li>Control the projects that can be mirrored to remote repositories</li>
                    <li>Put ${cfg.productName} into or out of maintenance mode</li>
                    <li>Use rPath Appliance Agent to perform system-level maintenance of ${cfg.productName}</li>
                </ul>

                <p>Note: Administrative operations for existing users and projects 
                    are available on each user/project home page. Find the 
                    desired user/project by searching or browsing, then 
                    navigate to the main page for the user/project.</p>
        </div>
    </body>
</html>
