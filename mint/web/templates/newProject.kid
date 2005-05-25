<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("New Project")}
    <body>
        ${header_image()}
        ${menu([("New Project", None, True)])}
        
        <div id="content">
            <h2>New Project</h2>       
 
            <form method="post" action="createProject">
                <table>
                    <tr>
                        <td><b>Project Title:</b></td>
                        <td><input type="text" name="title" /></td>
                    </tr>
                    <tr>
                        <td style="width: 25%;">
                            <b>Repository Hostname:</b>
                            <p class="help">
                                Please choose a hostname for your repository.
                                It must start with a letter and contain only
                                letters, numbers, and hyphens.
                            </p>
                        </td>
                        <td style="vertical-align: middle;">
                            <input type="text" name="hostname" /> .rpath.org
                        </td>
                    </tr>
                </table>

                <p><input type="submit" value="Create" /></p>
            </form>
            ${html_footer()}
        </div>
    </body>
</html>
