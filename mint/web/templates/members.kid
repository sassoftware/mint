<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    ${html_header("Manage Project Memberships")}
    <body>
        ${header_image()}
        ${menu([("Manage Project Memberships", None, True)])}
        <?python
            isOwner = userLevel == userlevels.OWNER
        ?>
        <div id="content">
            <h2>Manage Project Memberships</h2>

            <table>
                <tr>
                    <td><b>Project Name:</b></td>
                    <td>${project.getName()}</td>
                </tr>
                <tr>
                    <td style="width: 25%;">
                        <b>Members:</b>
                    </td>
                    <td>
                        <?python
                        users = { userlevels.DEVELOPER: [],
                                  userlevels.OWNER: [], }

                        for userId, username, level in project.getMembers():
                            users[level].append((userId, username,))

                        ?>
                        <h4>Project Owners</h4>
                        <ul>
                            <li py:for="userId, username in sorted(users[userlevels.OWNER], key=lambda x: x[1])">
                                <a href="userInfo?id=${userId}">${username}</a>
                                <a py:if="isOwner" href="memberSettings?userId=${userId}">[edit]</a>
                                <a py:if="isOwner" href="delMember?id=${userId}">[delete]</a>
                            </li>
                            <li py:if="not users[userlevels.OWNER]">No owners.</li>
                        </ul>
                        <h4>Developers</h4>
                        <ul>
                            <li py:for="userId, username in sorted(users[userlevels.DEVELOPER], key=lambda x: x[1])">
                                <a href="userInfo?id=${userId}">${username}</a>
                                <a py:if="isOwner" href="memberSettings?userId=${userId}">[edit]</a>
                                <a py:if="isOwner" href="delMember?id=${userId}">[delete]</a>
                            </li> 
                            <li py:if="not users[userlevels.DEVELOPER]">No developers.</li>
                        </ul>
                    </td>
                </tr>
                <tr py:if="isOwner">
                    <td>
                        <b>Add:</b>
                    </td>
                    <td> 
                        <form method="post" action="addMember">
                            <input type="text" name="username" value="" />
                            <select name="level">
                                <option py:for="level, levelName in userlevels.names.items()"
                                        py:content="levelName"
                                        value="${level}" />
                            </select>
                            <input type="submit" value="Submit" />
                        </form>
                    </td>
                </tr>
            </table>

            ${html_footer()}
        </div>
    </body>
</html>
