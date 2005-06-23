<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
import time
from mint import searcher
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("rpath.com")}
    <body>
        ${header_image()}
        ${menu([('rpath.com', False, True)])}

        <table style="width: 100%;">
            <tr><td style="padding: 0px;">

        <div id="content">
            <h2>rpath.com</h2>
            <p>This is a free service by rPath, Inc. to host Conary-managed Linux distributions. We will
               host a repository for your project and allow you to collaborate with others to create a complete
               Linux distribution almost entirely on the web.</p>

            <div py:if="not auth.authorized" py:omit="True">
                <p>To use this system, please <a href="register">register</a>.</p>

                <p>After you register, you will be able to create customized distributions based
                on the contents of your Conary repository.</p>

                <p>After you have registered, please <a href="login">log in</a>.</p>
            </div>

            <h3>Site News</h3>
            <ul>
                <li py:for="item in news"><a href="${item['link']}">${item['title']}</a> (${time.ctime(item['pubDate'])})</li>
            </ul>

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
            <form name="search" action="search" method="get">
                <span>Search Type:</span>
                <select name="type">
                    <option selected="selected" value="Projects">Search projects</option>
                    <option value="Users">Search users</option>
                </select>
                <br/>
                <span>Keyword(s):</span>
                <input type="text" name="search" size="10" />
                <br/>
                <span>Last modified:</span>
                <select name="modified">
                    <option py:for="i, option in enumerate(searcher.datehtml)" value="${i}">${option}</option>
                </select>
                <button>Submit</button>
            </form>

            <h3>Your Projects</h3>

            <ol id="active">
                <li py:for="project, level in sorted(projectList, key = lambda x: x[0].getName())">
                    <a href="http://${project.getHostname()}/">${project.getName()}</a> (${userlevels.names[level]})</li>
            </ol>
        </div>


        </td></tr></table>

    </body>
</html>

