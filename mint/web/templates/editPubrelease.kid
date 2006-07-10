<?xml version='1.0' encoding='UTF-8'?>

<?python
from mint import pubreleases
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="${basePath}releases">Releases</a>
        <a href="#">${(isNewRelease and "Create New" or "Edit") + " Release"}</a>
    </div>

    <head>
        <title>${formatTitle((isNewRelease and "Create New" or "Edit") + " Release")}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${projectsPane()}
                ${builderPane()}
            </div>

            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                <h2>${isNewRelease and "Create" or "Edit"} Release</h2>

                <form method="post" action="saveRelease" id="mainForm">

                    <div class="formgroupTitle">Release Information</div>
                    <div class="formgroup">
                        <label for="relname">Name</label>
                        <input id="relname" name="name" type="text" value="${release.name}" /><div class="clearleft">&nbsp;</div>

                        <label for="relver">Version</label>
                        <input id="relver" name="version" type="text" value="${release.version}" /><div class="clearleft">&nbsp;</div>

                        <label for="reldesc">Description (optional)</label>
                        <textarea id="reldesc" name="desc" type="text" py:content="release.description" /><div class="clearleft">&nbsp;</div>

                    </div>

                    <div class="formgroupTitle">Release Contents<span id="baton"></span></div>
                    <div class="formgroup">
                        TBD
                    </div>

                    <p>
                        <button id="submitButton" type="submit" py:attrs="{'disabled': isNewRelease and 'disabled' or None}">${isNewRelease and "Create" or "Recreate"} Release</button>
                    </p>
                    <input type="hidden" name="releaseId" value="${release.id}" />
                </form>
            </div>
        </div>
    </body>
</html>
