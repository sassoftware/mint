<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header(cfg, "Linux Mint")}
    <body>
        ${header_image(cfg)}
        ${menu([('Mint', False, True)])}

        <div id="content">
            <h2>${project.getName()}</h2>

            <h3>Project Details</h3>
            <code>${project.getDesc()}</code>
            
            <h3>Users</h3>

            <h3>Images</h3>

            ${html_footer()}
        </div>
    </body>
</html>

