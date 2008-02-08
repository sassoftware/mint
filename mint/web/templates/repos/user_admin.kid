<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">

    <!-- table of permissions -->
    <table class="user-admin" id="permissions" py:def="permTable(role, rows)">
        <thead>
            <tr>
                <td style="width: 55%;">Label</td>
                <td>Trove</td>
                <td>Write</td>
                <td py:if="cfg.removeTrovesVisible">Remove</td>
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
                <td py:if="cfg.removeTrovesVisible" py:content="row[3] and 'yes' or 'no'"/>
                <td><a href="deletePerm?role=${role};label=${row[0]}&amp;item=${row[1]}" title="Delete Permission">X</a></td>
                <td><a href="editPermForm?role=${role};label=${row[0]};trove=${row[1]};writeperm=${row[2]};remove=${row[3]}" title="Edit Permission">E</a></td>
            </tr>
            <tr py:if="not rows">
                <td>Role has no permissions.</td>
            </tr>
        </tbody>
    </table>

    <head>
        <title>${formatTitle('Manage Repository Permissions: %s'% project.getNameForDisplay(maxWordLen = 50))}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="spanright">
            <h2>Roles</h2>
            <table class="user-admin" id="roles">
                <thead><tr><td style="width: 25%;">Role Name</td><td>Admin</td><td>Mirror</td><td>Permissions</td><td style="text-align
: right;">Action</td></tr></thead>
                <tbody>
                    <tr py:for="i, role in enumerate([x for x in netAuth.getRoleList() if x != self.cfg.authUser])"
                        class="${i % 2 and 'even' or 'odd'}">
                    <?python #
                    rows = list(enumerate(netAuth.iterPermsByRole(role)))
                    ?>
                        <td><b>${role}</b></td>
                        <td py:if="netAuth.roleIsAdmin(role)" py:content="'yes'"/>
                        <td py:if="not netAuth.roleIsAdmin(role)" py:content="'no'"/>
                        <td py:if="netAuth.roleCanMirror(role)" py:content="'yes'"/>
                        <td py:if="not netAuth.roleCanMirror(role)" py:content="'no'"/>
                        <td py:if="rows" py:content="permTable(role, rows)"/>
                        <td py:if="not rows" style="font-size: 80%;">Role has no permissions</td>
                        <td style="text-align: right;">
                            <a href="addPermForm?roleName=${role}">Add Permission</a><br />
                            <a href="deleteRole?userRoleName=${role}">Delete</a> |
                            <a href="manageRoleForm?userRoleName=${role}">Manage</a>
                        </td>
                    </tr>
                </tbody>
            </table>
            <p>
                <a href="addRoleForm">Add Role</a>
            </p>
            </div>
        </div>
    </body>
</html>
