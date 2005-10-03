<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->

    <?python
        isOwner = userLevel == userlevels.OWNER or auth.admin
        memberList = project.getMembers()
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="#">Members</a>
    </div>

    <head>
        <title>${formatTitle('Member Settings: %s'%project.getName())}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
                <div class="palette" id="addmember" py:if="isOwner">

                    <h3 onclick="javascript:toggle_display('addmember_items');">
                        <img id="addmember_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_collapse.gif" border="0" />
                        Add New Member
                    </h3>
                    <div id="addmember_items" style="display: block">
                      <form method="post" action="addMember">
                        <p>
                            <label>Username:</label><br/>
                            <input type="text" name="username" value="" />
                        </p>
                        <p>
                            <label>Membership Type:</label><br/>

                            <select name="level">
                                <option py:for="level, levelName in sorted(userlevels.names.items(), reverse=True)"
                                        py:content="levelName"
                                        value="${level}" />
                            </select>
                        </p>
                        <p><button type="submit">Submit</button></p>
                      </form>
                    </div>
                </div>
                ${releasesMenu(project.getReleases(), isOwner, display="none")}
                ${commitsMenu(project.getCommits(), display="none")}
                ${browseMenu(display='none')}
                ${searchMenu(display='none')}
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

                lastOwner = len(users[userlevels.OWNER]) == 1 and len(users[userlevels.DEVELOPER]) > 0

                ?>
                <h3>Project Owners</h3>
                <table border="0" cellspacing="0" cellpadding="0" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.OWNER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="${cfg.basePath}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner and not lastOwner and userId != auth.userId">
                            <a href="demoteMember?userId=${userId}" class="option">Demote</a>
                        </td>
                        <td py:if="isOwner and not lastOwner and userId == auth.userId"></td>
                        <td py:if="isOwner and not lastOwner">
                            <a href="delMember?id=${userId}" class="option">Delete</a>
                        </td>
                    </tr>
                    <tr><td py:if="not users[userlevels.OWNER]">No owners.</td></tr>
                </table>
                <p class="help" py:if="isOwner and lastOwner and not auth.admin">
                    Because a project cannot have developers with no owner, you cannot change your
                    ownership status at this time. To remove yourself from this project, promote
                    a developer to Owner status, or orphan the project by removing all developers,
                    followed by yourself.
                </p>
                <h3>Developers</h3>

                <table border="0" cellspacing="0" cellpadding="0" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.DEVELOPER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="${cfg.basePath}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner">
                            <a href="promoteMember?userId=${userId}" class="option">Promote</a>
                        </td>
                        <td py:if="isOwner"><a href="delMember?id=${userId}" class="option">Delete</a></td>
                    </tr>
                    <tr><td py:if="not users[userlevels.DEVELOPER]">No developers.</td></tr>
                </table>
		<div py:if="reqList">
                    <h3>Requestors</h3>
                    <table border="0" cellspacing="0" cellpadding="0" class="memberstable">
                        <tr py:for="userId, username in reqList">
				<th><a href="${cfg.basePath}userInfo?id=${userId}">${username}</a></th>
                            <td>
                                <a href="viewJoinRequest?userId=${userId}"
                                   class="option" style="position:relative;"
                                   id="Edit${userId}">View Request</a>	
                            </td>
                        </tr>
                    </table>
		</div>
            </div>
        </td>
        ${projectsPane()}        
    </body>
</html>
