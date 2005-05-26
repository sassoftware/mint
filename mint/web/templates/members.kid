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
                        <td><b>Project Name:</b></td>
                        <td>${project.getName()}</td>
                    </tr>
                    <tr>
                        <td style="width: 25%;">
                            <b>Members:</b>
                        </td>
                        <td>
                            <ul>
                                <li py:for="userId, username, level in sorted(project.getMembers(), key=lambda x: x[1])">
                                    ${username} (a ${userlevels.names[level]})
                                    [<a py:if="userId != auth.userId" href="delMember?id=${userId}">remove</a>]
                                </li>
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
                        </td>
                    </tr>
                </table>

                <p><input type="submit" value="Submit" /></p>
            </form>
            ${html_footer()}
        </div>
    </body>
</html>
