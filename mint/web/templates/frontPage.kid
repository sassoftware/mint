<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("Linux Mint")}
    <body>
        ${header_image()}
        ${menu([('Mint', False, True)])}

        <table style="width: 100%;"> 
            <tr><td style="padding: 0px;">

        <div id="content"> 
            <h2>Linux Mint</h2>
            <p>The Linux Mint is a free service by rPath, Inc. to host Conary-managed Linux distributions. We will
               host a repository for your project and allow you to collaborate with others to create a complete
               Linux distribution almost entirely on the web.</p>

            <div py:if="not auth.authorized" py:omit="True">
                <p>To use this system, please <a href="register">register</a>.</p>

                <p>After you register, you will be able to create customized distributions based
                on the contents of your Conary repository.</p>

                <p>After you have registered, please <a href="login">log in</a>.</p>
            </div>

            <div py:if="auth.authorized" py:omit="True">
                <p>Thank you for logging in.</p>
                <h3>Things To Do</h3>
                <ul>
                    <li><a href="newProject">Create a new distribution project</a></li>
                    <li><a href="distros">Find an existing distribution</a></li>
                    <li><a href="userSettings">View your user page</a></li>
                </ul> 
            </div>

            ${html_footer()}
        </div>

        </td>

        <td style="width: 15%;">

        <div style="background: white; padding: 12px; color: black;">
            <h3>Search</h3>
            <p>Search for a project:</p>
            <input type="text" name="search" size="10" /> <button>Submit</button>

            <h3>Your Projects</h3>

            <ol id="active">
                <li py:for="project in sorted(projectList, key = lambda x: x.getName())">
                    <a href="http://${project.getHostname()}/">${project.getName()}</a></li>
            </ol>
        </div>


        </td></tr></table>

    </body>
</html>

