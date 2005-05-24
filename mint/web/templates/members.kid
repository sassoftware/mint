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
 
            <form method="post" action="editMembers">
                <table>
                    <tr>
                        <td>Project Name:</td>
                        <td><b>${project.getName()}</b></td>
                    </tr>
                    <tr>
                        <td style="width: 25%;">
                            <b>Members:</b>
                        </td>
                        <td style="vertical-align: middle;">
                            <ul>
                                <li py:for="userId, username in project.getMembers()">(${userId}) ${username}</li>
                            </ul>
                        </td>
                    </tr>
                    <tr><td>Add: <input type="text" name="username" value="" /></td></tr>
                </table>

                <p><input type="submit" value="Submit" /></p>
            </form>
            ${html_footer()}
        </div>
    </body>
</html>
