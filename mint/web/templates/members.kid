<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->

    <?python
        from mint.web.templatesupport import projectText
        from mint import userlevels
        isTrueOwner = userLevel == userlevels.OWNER
        isDeveloper = userLevel == userlevels.DEVELOPER
    ?>

    <head>
        <title>${formatTitle('Members: %s'%project.getNameForDisplay())}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                <div class="palette" id="members" py:if="isOwner">
                    <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
                    <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />

                    <div class="boxHeader"><span class="bracket">[</span> Add New Member <span class="bracket">]</span></div>
                    
                    <form method="post" action="${basePath}addMember">
                    <div class="memberBoxBody">
                        <label>Username:</label><br/>
                        <input type="text" name="username" value="" />
                        
                        <p>
                        <label for="level">Membership Type:</label><br/>
                        <select name="level">
                            <option py:if="hidden" py:for="level in reversed(userlevels.LEVELS)"
                                    py:content="userlevels.names[level]"
                                    value="${level}" />
                            <option py:if="not hidden" py:for="level in reversed(userlevels.WRITERS)"
                                    py:content="userlevels.names[level]"
                                    value="${level}" />
                        </select>
                        </p>
                        <div class="right"><button class="img" id="addMemberSubmit" type="submit"><img src="${cfg.staticPath}/apps/mint/images/add_member_button.png" alt="Add Member" /></button></div>
                    </div>
                    </form>
                </div>
                ${releasesMenu(projectPublishedReleases, isOwner)}
                ${commitsMenu(projectCommits)}
            </div>
            
            <div id="innerpage">
                <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${resourcePane()}
                    ${builderPane()}
                </div>
                <div id="middle">
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
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title">Members</div>
    
                    <div id="yourStatus" py:if="auth.authorized">
                        <h2>Your Status</h2>
                        <p py:if="userLevel == userlevels.NONMEMBER">
                            You are currently not involved in this ${projectText().lower()}.
                        </p>
                        <p py:if="userLevel == userlevels.USER">
                            You are currently a registered user of this ${projectText().lower()}.
                        </p>
                        <p py:if="userLevel == userlevels.DEVELOPER">
                            You are currently a developer of this ${projectText().lower()}.
                        </p>
                        <p py:if="userLevel == userlevels.OWNER">
                            You are currently ${onlyOwner and "the owner" or "an owner"} of this ${projectText().lower()}.
                        </p>
                        <p py:if="not isTrueOwner">Actions:
                        <ul class="pageSectionList">
                            <li py:if="auth.authorized and userLevel == userlevels.NONMEMBER">
                                <a href="${basePath}watch">Register</a> as a user of this ${projectText().lower()}</li>
                            <li py:if="userLevel == userlevels.USER">
                                <a href="${basePath}unwatch">Remove your registration</a> from this ${projectText().lower()}</li>
                                
                          <div py:strip="True" py:if="not project.external">
                            <li py:if="isWriter"><a href="${basePath}resign">Resign</a> from this ${projectText().lower()}</li>
                            <li py:if="auth.authorized and not isTrueOwner and not isDeveloper and True in [ x[2] not in userlevels.READERS for x in projectMemberList]">
                                <span py:if="not userHasReq"><a href="${basePath}joinRequest">Request to join</a> this ${projectText().lower()}</span>
                                <span py:if="userHasReq"><a href="${basePath}joinRequest">Modify your comments</a> to a pending join request</span></li>
                            <li py:if="True not in [ x[2] not in userlevels.READERS for x in projectMemberList]">
                                <span py:if="auth.authorized"><a href="${basePath}adopt">Adopt</a> this ${projectText().lower()}</span>
                                <span py:strip="True" py:if="not auth.authorized">Log in to adopt this ${projectText().lower()}</span></li>
                          </div>
                        </ul>
                        </p>
                    </div>
    
                    <h2>${projectText().title()} Owners</h2>
                    <table py:if="users[userlevels.OWNER]" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.OWNER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="http://${SITE}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner and not onlyOwner">
                            <a onclick="javascript:setUserLevel(${userId}, ${project.id}, ${userlevels.DEVELOPER});" 
                                href="#" class="option">Demote to Developer</a></td>
                        <td py:if="isOwner and not lastOwner"><a onclick="javascript:delMember(${project.id}, ${userId});" 
                            href="#" class="option">Remove From ${projectText().title()}</a></td>
                    </tr>
                    </table>
                    <p py:if="not users[userlevels.OWNER]">This ${projectText().lower()} has been orphaned.</p>
                    <p class="help" py:if="isTrueOwner and lastOwner">
                        Because a ${projectText().lower()} cannot have developers with no owner, you cannot change your
                        ownership status at this time. To remove yourself from this ${projectText().lower()}, promote
                        a developer to Owner status, or orphan the ${projectText().lower()} by removing all developers,
                        followed by yourself.
                    </p>
                    
                    <h2>Developers</h2>
                    <table py:if="users[userlevels.DEVELOPER]" class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.DEVELOPER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="http://${SITE}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner">
                        <a onclick="javascript:setUserLevel(${userId}, ${project.id}, ${userlevels.OWNER});" 
                            href="#" class="option">Promote to Owner</a></td>
                        <td py:if="isOwner"><a onclick="javascript:delMember(${project.id}, ${userId});" href="#" 
                            class="option">Remove From ${projectText().title()}</a></td>
                    </tr>
                    </table>
                    <p py:if="not users[userlevels.DEVELOPER]">This ${projectText().lower()} currently has no developers.</p>
                    
                    <div py:if="reqList">
                    <h2>Requestors</h2>
                    <table class="memberstable">
                    <tr py:for="userId, username in reqList">
                        <th><a href="http://${SITE}userInfo?id=${userId}">${username}</a></th>
                        <td>
                            <a href="viewJoinRequest?userId=${userId}" class="option" style="position:relative;"
                               id="Edit${userId}">View Request</a></td>
                    </tr>
                    </table>
                    </div>
                    
                    <h2>Users</h2>
                    <div py:if="isOwner" py:strip="True">
                    <table class="memberstable">
                    <tr py:for="userId, username in sorted(users[userlevels.USER], key=lambda x: x[1])">
                        <th><a py:strip="not auth.authorized" href="${cfg.basePath}userInfo?id=${userId}">${username}</a></th>
                        <td py:if="isOwner">
                            <a href="promoteMember?userId=${userId}" class="option">Promote to Developer</a></td>
                    </tr>
                    <tr>
                        <td py:if="not users[userlevels.USER]">Nobody has registered as a user of this ${projectText().lower()}</td>
                    </tr>
                    </table>
                    </div>
                    
                    <div py:if="not isOwner" py:strip="True">
                        <p py:if="not users[userlevels.USER]">Nobody has registered as a user of this ${projectText().lower()}.</p>
                        <p py:if="len(users[userlevels.USER]) == 1">There is one registered user of this ${projectText().lower()}.</p>
                        <p py:if="len(users[userlevels.USER]) > 1">There are ${len(users[userlevels.USER])} registered users of this ${projectText().lower()}.</p>
                    </div>
                    <div py:if="isWriter">
                        <h2>OpenPGP Signing Keys</h2>
                        <p>You can view the OpenPGP package signing keys that your developers have uploaded:</p>
                        <a class="pageSectionLink" href="../../repos/${project.hostname}/pgpAdminForm">${auth.admin and "Manage" or "View"} OpenPGP Signing Keys</a>
                    </div>
                </div><br class="clear" />
                <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
       </div>
    </body>
</html>
