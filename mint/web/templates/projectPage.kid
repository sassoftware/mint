<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("Linux Mint")}
    <?python
        isOwner = userLevel == userlevels.OWNER
    ?>
    <body>
        ${header_image()}
        ${menu([('Mint', False, True)])}

        <div id="content">
            <h2>${project.getName()}</h2>

            <h3>Project Details</h3>
            <p style="padding: 10px; border: 1px solid black;">
                <a class="button" style="float: right;" py:if="isOwner" href="projectDesc">Edit Description</a>
                ${project.getDesc()}
            </p>

            <div py:if="isOwner"><a href="http://${project.getHostname()}/conary/">Repository Administration</a></div>    
            <h3>Project Members</h3>
            <ul>
                <li py:for="userId, username, level in project.getMembers()">(${userId}) ${username}</li>
                <li py:if="isOwner"><a href="members">Manage Project Members</a></li>
            </ul>

            <h3>Releases</h3>
            <ul>
                <li>0.23</li>
                <li>0.24</li>
                <li>0.25</li>
                <li py:if="isOwner"><a href="http://iso.rpath.org/images/projectDetails?projectId=${project.getItProjectId()}">Release Management</a></li>
            </ul>

            <p py:if="isOwner">You are an owner of this project.</p>
            ${html_footer()}
        </div>
    </body>
</html>
