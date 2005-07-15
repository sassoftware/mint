<?xml version='1.0' encoding='UTF-8'?>
<?python from mint import userlevels ?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" class="pad">
        You are here:
        <a href="#">rpath</a>
        <a href="#">${user.getFullName()}</a>
    </div>

    <head/> 
    <body>
        <td id="left" class="plain">
            <div class="pad">
                <h3>${user.getFullName()}</h3>
                <p>${user.getDisplayEmail()}</p>
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <p py:for="line in user.getBlurb().splitlines()">
                    ${line}
                </p>
            </div>
        </td>
        <td id="right" class="plain">
            <div class="pad">
                <h3>this user's projects:</h3>
                <ul py:if="userProjects">
                    <li py:for="project, level in userProjects"><a href="http://${project.getHostname()}/">${project.getName()}</a> (${userlevels. names[level]})</li>
                </ul>
                <p py:if="not userProjects">This user is not a member of any projects.</p>
                <div class="palette">
                    <h3>add/edit project membership</h3>
                    <form method="post" action="editMember?userId=${auth.userId}">
                        <p>
                            <label>Select a project:</label><br/>
                            <select name="project">
                                <option selected="selected">Select a project...</option>
                            </select>
                        </p>
                        <p>
                            <label>Level:</label><br/>
                            <select name="level">
                                <option py:for="level, levelName in userlevels.names.items()"
                                        py:content="levelName"
                                        value="${level}"
                                        />
                            </select>
                        </p>
                        <p><button type="submit">Submit</button></p>
                    </form>
                </div>
            </div>
        </td>
    </body>
</html>
