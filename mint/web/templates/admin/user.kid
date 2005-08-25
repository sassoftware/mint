<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'administer.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        ${adminbreadcrumb()}
        <a href="#">User Administration</a>
    </div>

    <head>
        <title>${formatTitle('Administer Users')}</title>
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
              The list of user operations
              <ul>
                <li>Delete User</li>
                <li>Change Password</li>
                <li>Change Email Address</li>
              </ul>
            </div>
        </td>
    </body>
</html>
