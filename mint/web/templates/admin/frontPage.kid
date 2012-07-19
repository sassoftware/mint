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
        <title>${formatTitle('Administer')}</title>
    </head>
    <body>
        <div class="admin-page">
            <div id="left" class="side">
                ${adminResourcesMenu()}
            </div>
            <div id="admin-spanright">
                <div class="page-title-no-project">${cfg.productName} Administration</div>
    
                <p>This is the main ${cfg.productName} administration page. Using
                    the menu to the left, you can:</p>
    
                    <ul>
                        <li>Add ${projectText().lower()}s that reference remote repositories</li>
                        <li>Control the ${projectText().lower()}s that can be mirrored to remote repositories</li>
                        <li>Put ${cfg.productName} into or out of maintenance mode</li>
                        <li>Use rPath Appliance Agent to perform system-level maintenance of ${cfg.productName}</li>
                    </ul>
    
                    <p>Note: Administrative operations for existing users and ${projectText().lower()}s 
                        are available on each user/${projectText().lower()} home page. Find the 
                        desired user/${projectText().lower()} by searching or browsing, then 
                        navigate to the main page for the user/${projectText().lower()}.</p>
            </div>
            <div class="bottom"/>
        </div>
    </body>
</html>
