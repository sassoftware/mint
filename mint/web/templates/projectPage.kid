<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("rpath.com")}
    <?python
        isOwner = userLevel == userlevels.OWNER
    ?>
    <body>
        ${header_image()}
        ${menu([('rpath.com', False, True)])}

        <div id="content">
            <h2>${project.getName()}</h2>

            <h3>Project Details</h3>
            <p style="padding: 10px; border: 1px solid black;">
                <a class="button" style="float: right;" py:if="isOwner" href="projectDesc">Edit Description</a>
                ${project.getDesc()}
            </p>

            <div><a href="http://${project.getHostname()}/conary/browse">Browse Repository</a></div> 
            <h3>Project Members</h3>
            <?python 
              memberList = project.getMembers()
            ?>
            <p py:if="not memberList">This project is orphaned. <a href="adopt">Adopt this project</a></p>
            <p py:if="memberList"><a href="members">Click to see project members</a></p>

            <h3><a href="releases">Releases Page</a></h3>
            <ul>
                <li py:for="release in project.getReleases()">${release.getTroveName()}=${release.getTroveVersion().trailingRevision().asString()}</li>
            </ul>
            
            <p py:if="isOwner">You are an owner of this project.</p>
            ${html_footer()}
        </div>
    </body>
</html>
