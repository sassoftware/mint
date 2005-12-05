<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="adminbreadcrumb()" py:strip="True">
        <a href="administer">Administration</a>
    </div>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">Administration</a>
    </div>

    <head>
        <title>${formatTitle('Administer')}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${browseMenu()}
                ${searchMenu()}
            </div>
        </td>

        <td id="main" class="spanall">
            <div class="pad">
              <p py:if="kwargs.get('extraMsg', None) and not kwargs.get('errors',None)" class="message" py:content="kwargs['extraMsg']"/>
              <h2>Available operations</h2>
              <ul>
                <li><a href="administer?operation=user">User Operations</a></li>
                <li><a href="administer?operation=project">Project Operations</a></li>
                <li><a href="administer?operation=notify">Notify All Users</a></li>
                <li><a href="administer?operation=report">View Reports</a></li>
              </ul>
            </div>
        </td>
    </body>
</html>
