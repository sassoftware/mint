<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("Manage Project Memberships")}
    <body>
        ${header_image()}
        ${menu([("Manage Project Memberships", None, True)])}
        
        <div id="content">
            <h2>Manage Project Memberships</h2>       
 
            <form method="post" action="addMember">
                <table>
                    <tr>
                        <td><b>Project Name:</b></td>
                        <td>${project.getName()}</td>
                    </tr>
                    <tr>
                        <td style="width: 25%;">
                            <b>Members:</b>
                        </td>
                        <td>
                            <?python
                            users = { userlevels.DEVELOPER: [],
                                      userlevels.ADMIN: [], }

                            for userId, username, level in project.getMembers():
                                users[level].append((userId, username,))
            
                            ?>
                            <h4>Project Owners</h4>
                            <ul>
                                <li py:for="userId, username in sorted(users[userlevels.ADMIN], key=lambda x: x[1])">
                                    <a href="memberSettings?userId=${userId}">${username}</a>
                                </li>
                                <li py:if="not users[userlevels.ADMIN]">No owners.</li>
                            </ul>
                            <h4>Developers</h4>
                            <ul>
                                <li py:for="userId, username in sorted(users[userlevels.DEVELOPER], key=lambda x: x[1])">
                                    <a href="memberSettings?userId=${userId}">${username}</a>
                                </li> 
                                <li py:if="not users[userlevels.DEVELOPER]">No developers.</li>
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <b>Add:</b>
                            <p class="help"><a href="lookupUser">Look up user</a></p>
                        </td>
                        <td> 
                            <input type="text" name="username" value="" />
                            <select name="level">
                                <option py:for="level, levelName in userlevels.names.items()"
                                        py:content="levelName"
                                        value="${level}" />
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
