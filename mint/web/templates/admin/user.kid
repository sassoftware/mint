<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'administer.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        ${adminbreadcrumb()}
        <a href="administer?operation=user">User Administration</a>
    </div>

    <head>
        <title>${formatTitle('Administer Users')}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
              <p py:if="kwargs.get('extraMsg', None)" class="message" py:content="kwargs['extraMsg']"/>
              <form action="administer" method="post">
                <h2>Select a user below to modify</h2>
                <p>
                  <select name="userId">
                    <option py:for="user in userlist" value="${user[0]}" py:content="user[1]" py:attrs="{'class': not user[2] and 'hiddenOption' or None}"/>
                  </select>
                </p>
                <p>
                  <button name="operation" value="user_reset_password">Reset Password</button>
                  <button name="operation" value="user_cancel">Cancel User Account</button>
                </p>
              </form>
              <div>
                <h2>Other user operations</h2>
                <p><a href="administer?operation=user_new">Create a new user</a></p>
              </div>
            </div>
        </td>
    </body>
</html>
