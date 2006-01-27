<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->

    <?python
        isOwner = userLevel == userlevels.OWNER or auth.admin
        isDeveloper = userLevel == userlevels.DEVELOPER
        memberList = project.getMembers()
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="#">Members</a>
    </div>

    <head>
        <title>${formatTitle('Members: %s'%project.getNameForDisplay())}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad" >
                ${projectResourcesMenu()}
                <div class="palette" id="addmember" py:if="isOwner">
                    <h3 onclick="javascript:toggle_display('addmember_items');">
                        <img id="addmember_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_collapse.gif" class="noborder" />
                        Add New Member
                    </h3>
                    <div id="addmember_items" style="display: block">
                      <form method="post" action="${basePath}addMember">
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
            <div class="pad" >
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
                <h2>${project.getNameForDisplay(maxWordLen = 50)}<br/>
                    Members</h2>

                <div id="yourStatus" py:if="auth.authorized">
                    <h3>Your Status</h3>
                    <p py:if="userLevel == userlevels.NONMEMBER">
                        You are currently not involved in this project.
                    </p>
                    <p py:if="userLevel == userlevels.USER">
                        You are currently watching this project.
                    </p>
                    <p py:if="userLevel == userlevels.DEVELOPER">
                        You are currently a developer of this project.
                    </p>
                    <p py:if="userLevel == userlevels.OWNER">
                        You are currently ${onlyOwner and "the owner" or "an owner"} of this project.
                    </p>
                    <p py:if="not isOwner">Actions:
                        <ul>
                            <li py:if="auth.authorized and userLevel == userlevels.NONMEMBER">
                            <a href="${basePath}watch">Watch this project</a>
                            </li>
                            <li py:if="userLevel == userlevels.USER">
                                <a href="${basePath}unwatch">Stop watching this project</a>
                            </li>
                            <div py:strip="True" py:if="not project.external">
                                <li py:if="isDeveloper"><a href="${basePath}resign">Resign from this project</a></li>
                                <li py:if="auth.authorized and not isOwner and not isDeveloper and True in [ x[2] not in userlevels.READERS for x in memberList]">
                                    <a py:if="not userHasReq" href="${basePath}joinRequest">Request to join this project</a>
                                    <a py:if="userHasReq" href="${basePath}joinRequest">Modify your comments to a pending join request</a>
                                </li>
                                <li py:if="True not in [ x[2] not in userlevels.READERS for x in memberList]">
                                    <a py:if="auth.authorized" href="${basePath}adopt">Adopt this project</a>
                                    <span py:strip="True" py:if="not auth.authorized">Log in to adopt this project</span>
                                </li>
                            </div>
                        </ul>
                    </p>
                </div>

                <h3>Project Owners</h3>
                <table py:if="users[userlevels.OWNER]" border="0" cellspacing="0" cellpadding="0" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.OWNER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="http://${SITE}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner and not onlyOwner">
                            <a href="demoteMember?userId=${userId}" class="option">Demote to Developer</a>
                        </td>
                        <td py:if="isOwner and not lastOwner">
                            <a href="delMember?id=${userId}" class="option">Remove From Project</a> </td>
                    </tr>
                </table>
                <p py:if="not users[userlevels.OWNER]">This project has been orphaned.</p>
                <p class="help" py:if="isOwner and lastOwner and not auth.admin">
                    Because a project cannot have developers with no owner, you cannot change your
                    ownership status at this time. To remove yourself from this project, promote
                    a developer to Owner status, or orphan the project by removing all developers,
                    followed by yourself.
                </p>
                <h3>Developers</h3>

                <table py:if="users[userlevels.DEVELOPER]" border="0" cellspacing="0" cellpadding="0" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.DEVELOPER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="http://${SITE}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner">
                            <a href="promoteMember?userId=${userId}" class="option">Promote to Owner</a>
                        </td>
                        <td py:if="isOwner"><a href="delMember?id=${userId}" class="option">Remove From Project</a></td>
                    </tr>
                </table>
                <p py:if="not users[userlevels.DEVELOPER]">This project currently has no developers.</p>
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
                <h3>Users</h3>
                <div py:if="isOwner" py:strip="True">
                <table border="0" cellspacing="0" cellpadding="0" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.USER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="${cfg.basePath}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner">
                            <a href="promoteMember?userId=${userId}" class="option">Promote to Developer</a>
                        </td>
                    </tr>
                    <tr><td py:if="not users[userlevels.USER]">No users are watching this project</td></tr>
                </table>
                </div>
                <div py:if="not isOwner" py:strip="True">
                    <p py:if="not users[userlevels.USER]">There are no users watching this project.</p>
                    <p py:if="len(users[userlevels.USER]) == 1">There is one user watching this project.</p>
                    <p py:if="len(users[userlevels.USER]) > 1">There are ${len(users[userlevels.USER])} users watching this project.</p>
                </div>
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
