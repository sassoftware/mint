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
            
            <h3>Project Members</h3>
            <ul>
                <li py:for="userId, username in project.getMembers()">(${userId}) ${username}</li>
            </ul>

            <h3>Releases</h3>
            <ul>
                <li>0.23</li>
                <li>0.24</li>
                <li>0.25</li>
                <li py:if="project.getOwnerId() == auth.userId"><i>Release Management</i></li>
            </ul>

            <span py:omit="True" py:if="project.getOwnerId() == auth.userId">
                <h3>Owner Options</h3>
                <ul>
                    <li>Edit Project Details</li>
                    <li>Manage Project Members</li>
                </ul>
            </span>
            ${html_footer()}
        </div>
    </body>
</html>
