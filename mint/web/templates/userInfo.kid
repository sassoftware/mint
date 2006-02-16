<?xml version='1.0' encoding='UTF-8'?>
<?python 
  from mint import userlevels 
  from mint.helperfuncs import truncateForDisplay
 ?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <?python
        ownsProjects = False
        if projectList:
            for project, level in projectList:
                if level == userlevels.OWNER:
                    ownsProjects = True
                    break
    ?>

    <head>
        <title>${formatTitle('User Information: %s' % user.username)}</title>
    </head>

    <body>
        <div class="layout">
            <div id="right" class="side">
                ${resourcePane()}
		${groupTroveBuilder()}
                <div class="palette" py:if="ownsProjects and user.id != auth.userId">
                    <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
                    <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />

                    <div class="boxHeader">Add to Project</div>
                    <form method="post" action="addMemberById">
                        <p>
                            <label>Select a project:</label><br/>
                            <select name="projectId">
                                <option py:for="project, level in sorted(projectList, key = lambda x: x[0].getName())"
                                        py:if="level == userlevels.OWNER"
                                        value="${project.getId()}"
                                        py:content="project.getName()"/>
                            </select>
                        </p>
                        <p>
                            <label>Level:</label><br/>
                            <select name="level">
                                <option py:for="level, levelName in sorted(userlevels.names.items(), reverse = True)"
                                        py:content="levelName"
                                        value="${level}"
                                        />
                            </select>
                        </p>
                        <input type="hidden" name="userId" value="${user.getId()}" />
                        <p><button type="submit">Add ${user.username}</button></p>
                    </form>
                </div>
            </div>
            <div id="spanleft">
                <h2 py:if="user.fullName">${user.fullName} (${user.username})</h2>
                <h2 py:if="not user.fullName">${user.username}</h2>

                <h3>About ${user.username}:</h3>
                <p py:for="line in user.getBlurb().splitlines()">
                    ${truncateForDisplay(line, 1000000, 70)}
                </p>
                <div py:if="not user.getBlurb()">User has not entered any about text.</div>

                <h3>Contact Information:</h3>
                <p py:for="line in user.getDisplayEmail().splitlines()" py:strip="True">
                    ${truncateForDisplay(line, 1000000, 70)}
                </p>
                <div py:if="not user.getDisplayEmail()">User has not entered any contact information.</div>

                <h3>${user.getUsername()}'s projects:</h3>
                <ul py:if="userProjects">
                    <li py:for="project, level in userProjects">
                        <a
                            href="${project.getUrl()}">${project.getNameForDisplay()}</a>
                        (${userlevels. names[level]})
                    </li>
                </ul>
                <p py:if="not userProjects">This user is not a member of any projects.</p>

            </div>
        </div>
    </body>
</html>
