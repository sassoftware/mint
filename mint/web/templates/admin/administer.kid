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
              <h2>Available operations</h2>
              <ul>
                <li><a href="${cfg.basePath}administer?operation=user">User Operations</a></li>
                <li><a href="${cfg.basePath}administer?operation=project">Project Operations</a></li>
                <li><a href="${cfg.basePath}administer?operation=notify">Notify All Users</a></li>
                <li><a href="${cfg.basePath}administer?operation=report">View Reports</a></li>
                <li><a href="${cfg.basePath}administer?operation=external">Add External Project</a></li>
                <li><a href="${cfg.basePath}administer?operation=outbound">Manage Outbound Mirror Settings</a></li>
                <li><a href="${cfg.basePath}administer?operation=jobs">Manage Jobs</a></li>
                <li><a href="${cfg.basePath}administer?operation=maintenance_mode">Manage Maintenance Mode</a></li>
              </ul>
            </div>
        </td>
    </body>
</html>
