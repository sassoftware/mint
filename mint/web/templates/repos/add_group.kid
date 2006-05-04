<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
    <head>
        <title>${formatTitle('Repository Browser: %s'% project.getNameForDisplay(maxWordLen = 50))}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(project.getReleases(), isOwner)}
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="spanright">
            <h2 py:content="modify and 'Edit Group' or 'Add Group'"></h2>

            <form method="post" action="${modify and 'manageGroup' or 'addGroup'}">
                <input py:if="modify" type="hidden" name="userGroupName" value="${userGroupName}" />
                <table class="add-form">
                    <tr>
                        <td id="header">Group Name:</td>
                        <td><input type="text" name="newUserGroupName" value="${userGroupName}"/></td>
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
                        <td id="header">User can mirror:</td>
                        <td>
                            <input type="radio" name="canMirror" value="1" py:attrs="{'checked' : canMirror and 'checked' or None }"/>Yes
                            <input type="radio" name="canMirror" value="0" py:attrs="{'checked' : (not canMirror) and 'checked' or None }"/>No
                        </td>
                    </tr>
                </table>
                <p>
                    <input py:if="not modify" type="submit" value="Add Group" />
                    <input py:if="modify" type="submit" value="Submit Group Changes" />
                </p>
            </form>
            </div>
        </div>
    </body>
</html>
