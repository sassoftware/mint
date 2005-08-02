<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->

    <?python
        isOwner = userLevel == userlevels.OWNER
        memberList = project.getMembers()
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="/">${project.getName()}</a>
        <a href="#">Members</a>
    </div>

    <head/>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
                <div class="palette" py:if="isOwner">

                    <h3>Add New Member</h3>
                    <form method="post" action="addMember">
                        <p>
                            <label>Username:</label><br/>
                            <input type="text" name="username" value="" />
                        </p>
                        <p>
                            <label>Membership Type:</label><br/>

                            <select name="level">
                                <option py:for="level, levelName in userlevels.names.items()"
                                        py:content="levelName"
                                        value="${level}" />
                            </select>
                        </p>
                        <p><button type="submit">Submit</button></p>
                    </form>
                </div>
            </div>

        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br />Memberships</h2>
                <?python
                users = { userlevels.DEVELOPER: [],
                          userlevels.OWNER: [], }

                for userId, username, level in project.getMembers():
                    users[level].append((userId, username,))

                ?>
                <h3>Project Owners</h3>
                <table border="0" cellspacing="0" cellpadding="0" class="memberstable">

                    <tr py:for="userId, username in sorted(users[userlevels.OWNER], key=lambda x: x[1])">
                        <th><a href="userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner">
                            <a onclick="javascript:show_popup('Edit${userId}','memberEditBox');"
                               href="memberSettings?userId=${userId}"
                               class="option" style="position:relative;"
                               id="Edit${userId}" target="memberEditBox">Edit</a>
                        </td>
                        <td py:if="isOwner"><a href="delMember?id=${userId}" class="option">Delete</a></td>
                    </tr>
                </table>
                <h3>Developers</h3>

                <table border="0" cellspacing="0" cellpadding="0" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.DEVELOPER], key=lambda x: x[1])">
                        <th><a href="userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner">
                            <a onclick="javascript:show_popup('Edit${userId}','memberEditBox');"
                               href="memberSettings?userId=${userId}"
                               class="option" style="position:relative;"
                               id="Edit${userId}" target="memberEditBox">Edit</a>
                        </td>
                        <td py:if="isOwner"><a href="delMember?id=${userId}" class="option">Delete</a></td>
                    </tr>
                </table>
                <iframe src="about:blank" frameborder="0" marginheight="0" marginwidth="0"
                        scrolling="no" id="memberEditBox" name="memberEditBox" 
                        style="width:268px; position:absolute; z-index:115; visibility:hidden; overflow:hidden;"/>
            </div>
        </td>
        ${projectsPane()}        
    </body>
</html>
