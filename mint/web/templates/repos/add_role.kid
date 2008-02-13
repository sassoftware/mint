<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
    <head>
        <title>${formatTitle((modify and 'Edit' or 'Add') + ' Role: %s'% project.getNameForDisplay(maxWordLen = 50))}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="spanright">
            <h2 py:content="modify and 'Edit Role' or 'Add Role'"></h2>

            <form method="post" action="${modify and 'manageRole' or 'addRole'}">
                <input py:if="modify" type="hidden" name="roleName" value="${roleName}" />
                <table class="add-form">
                    <tr>
                        <td id="header">Role Name:</td>
                        <td><input type="text" name="newRoleName" value="${roleName}"/></td>
                    </tr>
                    <tr>
                        <td id="header">Initial Users:</td>
                        <td>
                            <select name="memberList" multiple="multiple" size="10"
                                    style="width: 100%;">
                                <option py:for="userName in [x for x in sorted(users) if x != self.cfg.authUser]"
                                        value="${userName}"
                                        py:attrs="{'selected': (userName in members) and 'selected' or None}">
                                    ${userName}
                                </option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td id="header">Role can mirror:</td>
                        <td>
                            <input type="radio" name="canMirror" value="1" py:attrs="{'checked' : canMirror and 'checked' or None }"/>Yes
                            <input type="radio" name="canMirror" value="0" py:attrs="{'checked' : (not canMirror) and 'checked' or None }"/>No
                        </td>
                    </tr>
                </table>
                <p>
                    <input py:if="not modify" type="submit" value="Add Role" />
                    <input py:if="modify" type="submit" value="Submit Role Changes" />
                </p>
            </form>
            </div>
        </div>
    </body>
</html>
