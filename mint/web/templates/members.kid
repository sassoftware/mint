<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
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
        <title>${formatTitle('Members: %s'%project.getName())}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
                <div class="palette" id="addmember" py:if="isOwner">

                    <h3 onclick="javascript:toggle_display('addmember_items');">
                        <img id="addmember_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_collapse.gif" class="noborder" />
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
                                <option py:for="level in reversed(userlevels.WRITERS)"
                                        py:content="userlevels.names[level]"
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
                <h2>${project.getName()}<br />Members</h2>
                <?python
                users = {
                          userlevels.OWNER: [], 
                          userlevels.DEVELOPER: [],
                          userlevels.USER: [],
                        }

                for userId, username, level in project.getMembers():
                    users[level].append((userId, username,))

                lastOwner = project.lastOwner(auth.userId)
                onlyOwner = project.onlyOwner(auth.userId)

                ?>
                <h3>Project Owners</h3>
                <table border="0" cellspacing="0" cellpadding="0" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.OWNER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="http://${SITE}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner and not onlyOwner">
                            <a href="demoteMember?userId=${userId}" class="option">Demote</a>
                        </td>
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
                        <th><a py:strip="not auth.authorized" href="http://${SITE}userInfo?id=${userId}">${username}</a></th>
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
				<th><a href="http://${SITE}userInfo?id=${userId}">${username}</a></th>
                            <td>
                                <a href="viewJoinRequest?userId=${userId}"
                                   class="option" style="position:relative;"
                                   id="Edit${userId}">View Request</a>	
                            </td>
                        </tr>
                    </table>
		</div>
                <div py:if="isOwner" py:strip="True">
                <h3>Users watching this project</h3>
                <table border="0" cellspacing="0" cellpadding="0" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.USER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="${cfg.basePath}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner">
                            <a href="promoteMember?userId=${userId}" class="option">Promote</a>
                        </td>
                    </tr>
                    <tr><td py:if="not users[userlevels.USER]">No users are watching this project</td></tr>
                </table>
                </div>
                <h3 py:if="not isOwner">
                    <div py:if="not users[userlevels.USER]" py:strip="True">There are no users watching this project</div>
                    <div py:if="len(users[userlevels.USER]) == 1" py:strip="True">There is one user watching this project</div>
                    <div py:if="len(users[userlevels.USER]) > 1" py:strip="True">There are ${len(users[userlevels.USER])} users watching this project</div>
                </h3>
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
            <div class="pad">
                ${groupTroveBuilder()}
            </div>
        </td> 
    </body>
</html>
