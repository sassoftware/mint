<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("Project Releases")}
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import userlevels

        isOwner = userLevel == userlevels.OWNER
        releases = project.getReleases()
    ?>
    <body>
        ${header_image()}
        ${menu([("Project Releases", None, True)])}
        
        <div id="content">
            <h2>Project Releases</h2>       
 
            <ul>
                <li py:for="release in releases">
                    <a href="http://iso.rpath.org/images/downloadRelease?profileId=${release.getId()}">${release.getTroveName()}=${release.getTroveVersion().trailingRevision().asString()}</a>
                </li>
            </ul>
            ${html_footer()}
        </div>
    </body>
</html>
