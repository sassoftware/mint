<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Administer Users')}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
              <p py:for=" errorMsg in kwargs.get('errors', [])" class="errormessage" py:content="errorMsg"/>
              <p py:if="kwargs.get('extraMsg', None)" class="message" py:content="kwargs['extraMsg']"/>
              <form action="${cfg.basePath}admin/processUserAction" method="post">
	        <a href="${cfg.basePath}admin">Return to Administrator Page</a>
                <h2>Select a user below to modify</h2>
                <p>
                  <select name="userId">
		     <option py:for="user in userlist" value="${user[0]}" py:content="user[1]" py:attrs="{'class': not user[2] and 'hiddenOption' or None}"/>
                  </select>
                </p>
                <p>
                  <button name="operation" value="user_reset_password">Reset Password</button>
                  <button name="operation" value="user_cancel">Cancel User Account</button>
                  <button name="operation" value="user_promote_admin">Promote To Administrator</button>
                  <button name="operation" value="user_demote_admin">Revoke Administrative Privileges</button>
                </p>
              </form>
              <div>
                <h2>Other user operations</h2>
                <p><a href="${cfg.basePath}admin/newUser">Create a new user</a></p>
              </div>
            </div>
        </td>
    </body>
</html>
