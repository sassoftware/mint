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
    ${html_header("User Information")}
    <body>
        ${header_image()}
        ${menu([('User Information', None, True)])}
        <div id="content">
            <h2>User Information:</h2>

            <table>
                <tr>
                    <td>Name:</td>
                    <td>${user.getFullName()}</td>
                </tr>
                <tr>
                    <td>Email Address:</td>
                    <td>${user.getDisplayEmail()}</td>
                </tr>
                <tr>
                    <td>Blurb:</td>
                    <td>
                        <p py:for="line in user.getBlurb().splitlines()">
                            ${line}
                        </p>
                    </td>
                </tr>

                <tr>
                    <td>Projects:</td>
                    <td>
                        <ul py:if="userProjects">
                            <li py:for="project, level in userProjects">
                                <a href="http://${project.getHostname()}/">${project.getName()}</a> (${userlevels.names[level]})
                            </li>
                        </ul>
                        <span py:if="not userProjects">This user is not a member of any projects.</span>
                    </td>
                </tr>
            </table>

            ${html_footer()}
        </div>
    </body>
</html>
