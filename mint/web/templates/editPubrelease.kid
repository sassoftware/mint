<?xml version='1.0' encoding='UTF-8'?>

<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint import pubreleases
from mint.web.templatesupport import projectText
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="${basePath}releases">Releases</a>
        <a href="#">${(releaseId and "Edit" or "Create New") + " Release"}</a>
    </div>

    <head>
        <title>${formatTitle((releaseId and "Edit" or "Create New") + " Release")}</title>
    </head>
    <body onload="buttonStatus();">
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
                <h2>${releaseId and "Edit" or "Create"} Release</h2>
                <p  py:if="availableBuilds" class="help" style="margin-bottom: 24px;">Use this page to ${releaseId and 'edit an existing' or 'create a'} release. Fields labeled with a <em class="required">red arrow</em> are required. In addition, one or more images must be selected from the Release Contents section${releaseId and 's' or ''}.</p>

                <form py:if="availableBuilds or currentBuilds" method="post" action="saveRelease" id="mainForm">

                    <div class="formgroupTitle">Release Information</div>
                    <div class="formgroup">
			<div style="height: 1%;">
                        <label for="relname"><em class="required">Name</em></label>
                        <input id="relname" name="name" type="text" value="${name}" onkeyup="buttonStatus();"/>
                        <label for="namehelp">&nbsp;</label><span id="namehelp" style="width: 50%;" class="help">Enter a name for this release.</span>
			</div>
                        <div style="line-height: 20px;" class="clearleft">&nbsp;</div>
			<div style="height: 1%;">
                        <label for="relver"><em class="required">Version</em></label>
                        <input id="relver" name="version" type="text" value="${version}" onkeyup="buttonStatus();"/>
                        <label for="verhelp">&nbsp;</label><span id="verhelp" class="help">Enter a version for this release. (Example: 1.1.1)</span><div class="clearleft">&nbsp;</div>
			</div>

			<div style="height: 1%;">
                        <label for="reldesc">Description (optional)</label>
                        <textarea id="reldesc" name="desc" type="text" py:content="desc" />
                        <label for="deschelp">&nbsp;</label><span id="deschelp" class="help">Enter a description of the release here.  This field is optional.</span>
			</div>
                        <div style="line-height: 0;" class="clearleft">&nbsp;</div>

                    </div>


                    <div strip="True" py:if="currentBuilds">
                    <div class="formgroupTitle">Current Release Contents</div>
                    <div class="formgroup">
                    <p class="help" style="margin-left: 20px;
                    margin-right: 10px; margin-top: -5px;
                    margin-bottom: 5px;">The following images are
                    currently included in this release. Un-check an image to remove it.</p>
                        <?python from mint import buildtypes ?>
                        <?python rowStyle = 0 ?>
                        <div  py:attrs="{'class': rowStyle and 'odd' or 'even'}"  py:for="build in currentBuilds">
                        <label style="margin-left: 0px; text-align: left; margin-top: 5px; margin-bottom: 0px; width: 80%;"><a style="text-decoration: none; font-weight: bold; margin-left: 20px;" href="javascript:toggle_display('div_${build.getId()}');">${build.getName()}&#32;<img class="noborder" id="div_${build.getId()}_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif"/>
                        <div py:if="build.getBuildType() != buildtypes.IMAGELESS" class="smallSpecs" id="${build.getId()}_short">${build.getArch()}&nbsp;${buildtypes.typeNamesShort[build.getBuildType()]}&nbsp;&nbsp;&nbsp;${build.getDefaultName()}</div>
                        <div py:if="build.getBuildType() == buildtypes.IMAGELESS" class="smallSpecs" id="${build.getId()}_short">&nbsp;${buildtypes.typeNamesShort[build.getBuildType()]}&nbsp;&nbsp;&nbsp;${build.getDefaultName()}</div>
                        </a></label> 
                        <input type="checkbox" checked="True" class="relCheck" name="buildIds" value="${build.getId()}" onclick="buttonStatus();"/>
                            <div class="clearleft" style="line-height: 0">&nbsp;</div>
                        <div id="div_${build.getId()}" style="display: none;">
			    <div style="height: 1%">
                            <label class="troveSpecs">Group</label>
                            <div class="troveData">${build.getTroveName()}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
                            <label class="troveSpecs">Version</label>
                                <div class="troveData">${build.getTroveVersion()}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
			    <div>
                            <label class="troveSpecs">Flavor</label>
                            <div class="troveData">${str(build.getTroveFlavor()).replace(',', ', ')}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
                            </div>
                            <label class="troveSpecs">Architecture</label>
                            <div py:if="build.getBuildType() != buildtypes.IMAGELESS" class="troveData">${build.getArch()}</div>
                            <div py:if="build.getBuildType() == buildtypes.IMAGELESS" class="troveData">N/A</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
                            <label class="troveSpecs">Release Type</label>
                            <div class="troveData">${buildtypes.typeNames[build.getBuildType()]}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
                            <label class="troveSpecs">Image Notes</label>
                            <div class="troveData">${build.getDesc() and build.getDesc() or 'None'}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
                            
                        </div>
                        <?python rowStyle ^= 1 ?>
                        </div>
                    </div>
                    </div>

                    <div py:if="availableBuilds" py:strip="True">
                    <div class="formgroupTitle">${releaseId and 'Available Images' or 'Release Contents'}<span id="baton"></span></div>
                    <div class="formgroup">
                    <p class="help" style="margin-right: 10px; margin-left: 20px; margin-top: -5px; margin-bottom: 5px;">${releaseId and 'The following images are currently not included with this release. Check a release to add it.' or 'Select images to be included with this release.'}</p>
                        <?python from mint import buildtypes ?>
                        <?python rowStyle = 0 ?>
                        <div  py:attrs="{'class': rowStyle and 'odd' or 'even'}"  py:for="build in availableBuilds">
                        <label style="margin-left: 0px; text-align: left; margin-top: 5px; margin-bottom: 0px; width: 80%;"><a style="text-decoration: none; font-weight: bold; margin-left: 20px;" href="javascript:toggle_display('div_${build.getId()}');">${build.getName()}&#32;<img class="noborder" id="div_${build.getId()}_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif"/>
                                <div id="${build.getId()}_short" class="smallSpecs">${build.getArch()}&nbsp;${buildtypes.typeNamesShort[build.getBuildType()]}&nbsp;&nbsp;&nbsp;${build.getDefaultName()}</div>
                        </a></label>
                        <input type="checkbox" class="relCheck" name="buildIds" value="${build.getId()}" onclick="buttonStatus();"/>
                            <div class="clearleft" style="line-height: 0">&nbsp;</div>
                        <div id="div_${build.getId()}" style="display: none;">
			    <div style="height: 1%">
                            <label class="troveSpecs">Group</label>
                            <div class="troveData"> ${build.getTroveName()}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
                            <label class="troveSpecs">Version</label>
                                <div class="troveData"> ${build.getTroveVersion()}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
                            <label class="troveSpecs">Flavor</label>
                            <div class="troveData">${str(build.getTroveFlavor()).replace(',', ', ')}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
                            <label class="troveSpecs">Architecture</label>
                            <div class="troveData">${build.getArch()}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
                            <label class="troveSpecs">Release Type</label>
                            <div class="troveData">${buildtypes.typeNames[build.getBuildType()]}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
			    <div style="height: 1%">
                            <label class="troveSpecs">Image Notes</label>
                            <div class="troveData">${build.getDesc() and build.getDesc() or 'None'}</div>
                            <div class="clearleft" style="line-height: 0; clear: right;">&nbsp;</div>
                            <br/>
			    </div>
                           </div> 
                        <?python rowStyle ^= 1 ?>
                        </div>
                    </div>
                    </div>

                    <p>
                        <button id="submitButton" type="submit" py:attrs="{'disabled': not releaseId and 'disable' or None}">${releaseId and "Update" or "Create"} Release</button>
                    </p>
                    <?python
                        # hacktastic way of not passing a None through a request
                        if not releaseId:
                            releaseId = 0
                    ?>
                    <input type="hidden" name="id" value="${releaseId}" />
                </form>
                <p py:if="not (availableBuilds or currentBuilds)" class="help">There are currently no available images associated with this ${projectText().lower()} that contain downloadable files. One or more available images that contain downloadable files are required to create a release.  Click <a href="${basePath}builds">here</a> to create a new image.</p>
            </div>
        </div>
    </body>
</html>
