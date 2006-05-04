<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">

    <!-- table of permissions -->
    <table class="user-admin" id="permissions" py:def="permTable(group, rows)">
        <thead>
            <tr>
                <td style="width: 55%;">Label</td>
                <td>Trove</td>
                <td>Write</td>
                <td>Capped</td>
                <td>Admin</td>
                <td>X</td>
                <td>E</td>
            </tr>
        </thead>
        <tbody>
            <tr py:for="i, row in rows"
                class="${i % 2 and 'even' or 'odd'}">
                <td py:content="row[0]"/>
                <td py:content="row[1]"/>
                <td py:content="row[2] and 'yes' or 'no'"/>
                <td py:content="row[3] and 'yes' or 'no'"/>
                <td py:content="row[4] and 'yes' or 'no'"/>
                <td><a href="deletePerm?group=${group};label=${row[0]}&amp;item=${row[1]}" title="Delete Permission">X</a></td>
                <td><a href="editPermForm?group=${group};label=${row[0]};trove=${row[1]};writeperm=${row[2]};capped=${row[3]};admin=${row[4]}" title="Edit Permission">E</a></td>
            </tr>
            <tr py:if="not rows">
                <td>Group has no permissions.</td>
            </tr>
        </tbody>
    </table>

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
            <h2>Groups</h2>
            <table class="user-admin" id="groups">
                <thead><tr><td style="width: 25%;">Group Name</td><td>Mirror</td><td>Permissions</td><td style="text-align: right;">Options</td></tr></thead>
                <tbody>
                    <tr py:for="i, group in [x for x in enumerate(netAuth.getGroupList()) if x[1] != self.cfg.authUser]"
                        class="${i % 2 and 'even' or 'odd'}">
                    <?python #
                    rows = list(enumerate(netAuth.iterPermsByGroup(group)))
                    ?>
                        <td><b>${group}</b></td>
                        <td py:if="netAuth.groupCanMirror(group)" py:content="'yes'"/>
                        <td py:if="not netAuth.groupCanMirror(group)" py:content="'no'"/>
                        <td py:if="rows" py:content="permTable(group, rows)"/>
                        <td py:if="not rows" style="font-size: 80%;">Group has no permissions</td>
                        <td style="text-align: right;">
                            <a href="addPermForm?userGroupName=${group}">Add Permission</a><br />
                            <a href="deleteGroup?userGroupName=${group}">Delete</a> |
                            <a href="manageGroupForm?userGroupName=${group}">Manage</a>
                        </td>
                    </tr>
                </tbody>
            </table>
            <p>
                <a href="addGroupForm">Add Group</a>
            </p>
            </div>
        </div>
    </body>
</html>
