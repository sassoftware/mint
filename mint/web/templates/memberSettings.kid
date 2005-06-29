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
    ${html_header("Member Settings")}
    <body>
        ${header_image()}
        ${menu([('Member Settings', None, True)])}
        <div id="content">
            <h2>Member Settings:</h2>

            <form method="post" action="editMember?userId=${userId}">
                <table>
                    <tr>
                        <td>Name:</td>
                        <td>${user.getFullName()} ${user.getUsername()}</td>
                    </tr>
                    <tr>
                        <td>Level:</td>
                        <td>
                            <select name="level">
                                <option py:for="level, levelName in userlevels.names.items()"
                                        py:content="levelName"
                                        value="${level}"
                                        py:attrs="{'selected': level == otherUserLevel and 'selected' or None}" />
                            </select>
                        </td>
                    </tr>
                </table>

                <p><input type="submit" value="Submit" /></p>
            </form>
            ${html_footer()}
        </div>
    </body>
</html>
