<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Administer')}</title>
    </head>
    <?python # kid bug requires comment.
        from mint import maintenance
    ?>
    <body>
        <div class="admin-page">
            <div id="left" class="side">
                ${adminResourcesMenu()}
            </div>
            <div id="admin-spanright">
                <div class="page-title-no-project">Manage Maintenance Mode</div>
                <p>
                    Current Condition:&nbsp;
                    <b style="color: red;" py:if="maintenance.getMaintenanceMode(cfg)==maintenance.LOCKED_MODE">Maintenance Mode</b>
                    <b style="color: green;" py:if="maintenance.getMaintenanceMode(cfg)==maintenance.NORMAL_MODE">Operating Normally</b>

                </p>
                <form action="${cfg.basePath}admin/toggleMaintLock" method="post">
                <p>
                    <button type="submit">${maintenance.getMaintenanceMode(cfg)==maintenance.LOCKED_MODE and "Restore Normal Operation" or "Invoke Maintenance Mode"}</button>
                    <input type="hidden" name="curMode" value="${maintenance.getMaintenanceMode(cfg)}" />
                </p>
                </form>
            </div>
            <div class="bottom"/>
        </div>
    </body>
</html>
