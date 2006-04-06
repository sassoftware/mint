<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Administer')}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
              <p py:if="kwargs.get('extraMsg', None) and not kwargs.get('errors',None)" class="message" py:content="kwargs['extraMsg']"/>
              <a href ="${cfg.basePath}administer">Return to Administrator Page</a>
              <h2>Current Condition:&nbsp;
              <b style="color: red;" py:if="cfg.maintenanceMode">Maintenance Mode</b>
              <b style="color: green;" py:if="not cfg.maintenanceMode">Operating Normally</b>
              </h2>
              <form action="${cfg.basePath}administer" method="post">
                <p>
                  <button name="operation" value="toggle_maintenance_lock">${cfg.maintenanceMode and "Restore Normal Operation" or "Invoke Maintenance Mode"}</button>
                </p>
              </form>
            </div>
        </td>
    </body>
</html>
