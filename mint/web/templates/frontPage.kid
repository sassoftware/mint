<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header(cfg, "Linux Mint")}
    <body>
        ${header_image(cfg)}
        ${menu([('Mint', False, True)])}

        <table style="width: 100%;"> 
            <tr><td style="padding: 0px;">

        <div id="content"> 
            <h2>Linux Mint</h2>
            <p>The Linux Mint is a free service by rPath, Inc. to host Conary-managed Linux distributions. We will
               host a repository for your project and allow you to collaborate with others to create a complete
               Linux distribution almost entirely on the web.</p>

            <p>To use this system, please <a href="register">register</a>.</p>

            <p>After you register, you will be able to create customized distributions based
            on the contents of your Conary repository.</p>

            <p>After you have registered, please <a href="login">log in</a>.</p>

            ${html_footer()}
        </div>

        </td>

        <td>

        <div style="background: white; padding: 12px; color: black;">
            <h3>Search</h3>
            <p>Search for a project:</p>
            <input type="text" name="search" size="10" /> <button>Submit</button>

            <h3>Site News</h3>

            <ul id="news">
                <li>Browser-crashing bug fixed.</li>
                <li>rMint launched!</li>
            </ul>

            <h3>Popular Projects</h3>

            <ol id="active">
                <li>Foresight Linux</li>
                <li>rPath Linux</li>
                <li>Tiny Router Linux</li>
                <li>MythTV Linux</li>
            </ol>
        </div>


        </td></tr></table>

    </body>
</html>

