<?xml version='1.0' encoding='UTF-8'?>
<?python from mint import userlevels ?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <?python
        ownsProjects = False
        for project, level in projectList:
            if level == userlevels.OWNER:
                ownsProjects = True
                break
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">${user.getFullName()}</a>
    </div>

    <head>
        <title>rpath.org: user information</title>
    </head>

    <body>
        <td id="left" class="side">
            <div class="pad">
                ${browseMenu()}
            ${searchMenu()}
            </div>
        </td>

        <td id="main">
          <span style="float:left;">
            <div class="pad">
                <h3>${user.getFullName()} (${user.getUsername()})</h3>
                <div py:for="line in user.getDisplayEmail().splitlines()" py:strip="True">
                    ${line}<br/>
                </div>
                <div py:if="not user.getDisplayEmail()">User has not entered any contact information.</div>
            </div>
          </span>
          <span syle="float:right">
            <div class="pad">
                <p py:for="line in user.getBlurb().splitlines()">
                    ${line}
                </p>
                <p py:if="not user.getBlurb()">User has not entered any about text.</p>
            </div>
          </span>
        </td>
        <td id="right" class="projects">
            <div class="pad">
                <h3>${user.getUsername()}'s projects:</h3>
                <ul py:if="userProjects">
                    <li py:for="project, level in userProjects">
                        <a href="http://${project.getFQDN()}/">${project.getName()}</a>
                        (${userlevels. names[level]})
                    </li>
                </ul>
                <p py:if="not userProjects">This user is not a member of any projects.</p>
                <div class="palette" py:if="ownsProjects and user.id != auth.userId">
                    <h3>add ${user.getUsername()} to your project</h3>
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
                        <p><button type="submit">Submit</button></p>
                    </form>
                </div>
            </div>
        </td>
    </body>
</html>
