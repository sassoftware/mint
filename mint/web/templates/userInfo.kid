<?xml version='1.0' encoding='UTF-8'?>
<?python 
  from mint import userlevels 
  from mint.client import timeDelta
  from mint.helperfuncs import truncateForDisplay
  from mint.web.templatesupport import projectText
 ?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <?python
        ownsProjects = False
        if projectList:
            for project, level, memberReqs in projectList:
                if level == userlevels.OWNER:
                    ownsProjects = True
                    break
    ?>

    <head>
        <title>${formatTitle('User Information: %s' % user.username)}</title>
    </head>

    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            <div id="right" class="side">
                ${resourcePane()}
		        ${builderPane()}
                <div class="right-palette" py:if="ownsProjects and user.id != auth.userId">
                    <img class="left" src="${cfg.staticPath}apps/mint/images/header_user_left.png" alt="" />
                    <img class="right" src="${cfg.staticPath}apps/mint/images/header_user_right.png" alt="" />

                    <div class="rightBoxHeader">
                        Add to ${projectText().title()}
                    </div>
                    <div class="rightBoxBody">
                        <form method="post" action="addMemberById">
                            <label>Select a project:</label><br/>
                            <select name="projectId" id="select-add-user">
                                <option py:for="project, level, memberReqs in sorted(projectList, key = lambda x: x[0].getName())"
                                        py:if="level == userlevels.OWNER"
                                        value="${project.getId()}"
                                        py:content="project.getName()"/>
                            </select>
                            <p>
                            <label>Level:</label><br/>
                            <select name="level">
                                <option py:for="level, levelName in sorted(userlevels.names.items(), reverse = True)"
                                        py:content="levelName"
                                        value="${level}"
                                        />
                            </select></p>
                            <input type="hidden" name="userId" value="${user.getId()}" />
                            <p><button type="submit" class="img"><img src="${cfg.staticPath}/apps/mint/images/add_user.png" alt="Add User" /></button></p>
                            
                        </form>
                    </div>
                </div>
            </div>
           <div id="leftcenter">
                <?python
                    if user.fullName:
                        displayUserString = "%s (%s)" % (user.fullName, user.username)
                    else:
                        displayUserString = "%s" % user.username
                ?>
                <h1 class="search">About ${displayUserString}</h1>
                <p py:for="line in user.getBlurb().splitlines()">
                    ${truncateForDisplay(line, 1000000, 70)}
                </p>
                <div py:if="not user.getBlurb()">User has not entered any about text.</div>

                <h2>Contact Information</h2>
                <p py:for="line in user.getDisplayEmail().splitlines()" py:strip="True">
                    ${truncateForDisplay(line, 1000000, 70)}
                </p>
                <div py:if="not user.getDisplayEmail()">User has not entered any contact information.</div>
                
                <h2>${projectText().title()}s</h2>
                <ul py:if="userProjects">
                    <li py:for="project, level, memberReq in userProjects">
                        <a
                            href="${project.getUrl()}">${project.getNameForDisplay()}</a>
                        (${userlevels. names[level]})
                    </li>
                </ul>
                <p py:if="not userProjects">This user is not a member of any ${projectText().lower()}s.</p>
                
                
                <div py:if="auth.admin" py:strip="True">
                    <h2>User Status</h2>

                    <p>Account was created ${timeDelta(user.timeCreated, capitalized=False)}<span py:if="user.timeAccessed"> and was last accessed ${timeDelta(user.timeAccessed, capitalized=False)}</span>.</p>
                    <p py:if="user.active != 1">This user's account has not been confirmed yet.</p>
                    <p py:if="userIsAdmin">This user is a site administrator.</p>
                    <div py:if="auth.admin and (user.getId() != auth.userId)" py:strip="True">
                    <h2>Administrative Options</h2>
                    <p><form action="${cfg.basePath}processUserAction" method="post">
                        <label for="userAdminOptions">Choose an action:&nbsp;</label>
                        <select id="userAdminOptions" name="operation">
                            <option value="user_noop" selected="selected">--</option>
                            <option value="user_reset_password">Reset Password</option>
                            <option value="user_cancel">Cancel Account</option>
                            <option py:if="not userIsAdmin" value="user_promote_admin">Grant Administrative Privileges</option>
                            <option py:if="userIsAdmin" value="user_demote_admin">Revoke Administrative Privileges</option>

                        </select>
                        <button id="userAdminSubmitButton" type="submit">Go</button>
                        <input type="hidden" name="userId" value="${user.getId()}" />
                    </form></p>
                    </div>
                </div>


            </div><br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"></div>
        </div>
    </body>
</html>
