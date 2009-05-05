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
            
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${projectsPane()}
                </div>

            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                <div class="page-title">${releaseId and "Edit" or "Create"} Release</div>
                
                <p  py:if="availableBuilds" class="help" style="margin-bottom: 24px;">Use this page to ${releaseId and 'edit an existing' or 'create a'} release. Fields labeled with a <em class="required">red arrow</em> are required. In addition, one or more images must be selected from the Release Contents section${releaseId and 's' or ''}.</p>

                <form py:if="availableBuilds or currentBuilds" method="post" action="saveRelease" id="mainForm">

                    <h2>Release Information</h2>
                    <div class="formgroup">
			            <table class="formgrouptable">
                        <tr>
                            <td class="form-label"><em class="required">Name:</em></td>
                            <td width="100%"><input id="relname" name="name" type="text" value="${name}" onkeyup="buttonStatus();"/><br/>
                            <span id="namehelp" class="help">Enter a name for this release.</span></td>
                        </tr>
                        <tr>
                            <td class="form-label"><em class="required">Version:</em></td>
                            <td><input id="relver" name="version" type="text" value="${version}" onkeyup="buttonStatus();"/><br/>
                            <span id="verhelp" class="help">Enter a version for this release. (Example: 1.1.1)</span></td>
                        </tr>
                        <tr>
                            <td class="form-label">Description:&nbsp;</td>
                            <td><textarea id="reldesc" name="desc" type="text" py:content="desc" /><br/>
                            <span id="deschelp" class="help">Enter a description of the release here.  This field is optional.</span></td>
                        </tr>
                        </table>
                    </div>


                    <div strip="True" py:if="currentBuilds">
                        <h2>Current Release Contents</h2>
                        <div class="formgroup">
                            <p class="help" style="margin-left:20px; margin-right:10px; margin-top:-5px; margin-bottom: 5px;">
                            The following images are currently included in this release. Un-check an image to remove it.</p>
                            <?python from mint import buildtypes ?>
                            <?python rowStyle = 0 ?>
                            
                            <table class="image-table">
                            <div py:for="build in currentBuilds" py:strip="True">
                            
                            <tr py:attrs="{'class': rowStyle and 'odd' or 'even'}" >
                                <td>
                                    <a href="javascript:toggle_display('div_${build.getId()}');">
                                        <img class="noborder" id="div_${build.getId()}_expander" 
                                        src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif"/></a></td>
                                <td width="100%">
                                    <a class="image-list" href="javascript:toggle_display('div_${build.getId()}');">${build.getName()}&#32;
                                    <div py:if="build.getBuildType() != buildtypes.IMAGELESS" class="smallSpecs" id="${build.getId()}_short">
                                        ${build.getArch()} ${buildtypes.typeNamesShort[build.getBuildType()]} ${build.getDefaultName()}
                                    </div>
                                    <div py:if="build.getBuildType() == buildtypes.IMAGELESS" class="smallSpecs" id="${build.getId()}_short">
                                        ${buildtypes.typeNamesShort[build.getBuildType()]} ${build.getDefaultName()}
                                    </div></a></td>
                                <td class="rel-checkbox">
                                    <input class="relcheck" checked="checked" type="checkbox" name="buildIds" value="${build.getId()}" onclick="buttonStatus();"/></td>
                            </tr>
                            <tr py:attrs="{'class': rowStyle and 'odd' or 'even'}" >
                                <td></td>
                                <td colspan="2">
                                <div id="div_${build.getId()}" style="display: none;">
                                    <table class="formgrouptable">
                                    <tr>
                                        <td class="form-label"><b>Group:</b></td>
                                        <td width="100%">${build.getTroveName()}</td>
                                    </tr>
                                    <tr>
                                        <td class="form-label"><b>Version:</b></td>
                                        <td>${build.getTroveVersion()}</td>
                                    </tr>
    			                    <tr>
                                        <td class="form-label"><b>Flavor:</b></td>
                                        <td>${str(build.getTroveFlavor()).replace(',', ', ')}</td>
                                    </tr>
        			                <tr>
                                        <td class="form-label"><b>Architecture:</b></td>
                                        <td>
                                           <div  py:if="build.getBuildType() != buildtypes.IMAGELESS" class="troveData">${build.getArch()}</div>
                                           <div  py:if="build.getBuildType() == buildtypes.IMAGELESS" class="troveData">N/A</div></td>
                                    </tr>
        			                <tr>
                                        <td class="form-label"><b>Release Type:</b></td>
                                        <td>${buildtypes.typeNames[build.getBuildType()]}</td>
                                    </tr>
        			                <tr>
                                        <td class="form-label"><b>Image Notes:</b></td>
                                        <td>${build.getDesc() and build.getDesc() or 'None'}</td>
                                    </tr>
        			                </table><br/>
                                </div>
                                </td>
                            </tr>
                            <?python rowStyle ^= 1 ?>
                            </div>
                            </table>
                        </div>
                    </div>

                    <div py:if="availableBuilds" py:strip="True">
                    <h2>${releaseId and 'Available Images' or 'Release Contents'} <span id="baton"></span></h2>
                    
                    <div class="formgroup">
                        <p class="help" style="margin-right: 10px; margin-left: 20px; margin-top: -5px; margin-bottom: 5px;">
                    ${releaseId and 'The following images are currently not included with this release. Check a release to add it.' or 'Select images to be included with this release.'}</p>

                        <?python from mint import buildtypes ?>
                        <?python rowStyle = 0 ?>
                        
                        <table class="image-table">
                        <div py:for="build in availableBuilds" py:strip="True">
                        
                        <tr py:attrs="{'class': rowStyle and 'odd' or 'even'}">
                            <td>
                                <a href="javascript:toggle_display('div_${build.getId()}');">
                                    <img class="noborder" id="div_${build.getId()}_expander" 
                                    src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif"/></a></td>
                            <td width="100%">
                                <a class="image-list" href="javascript:toggle_display('div_${build.getId()}');">${build.getName()}&#32;
                                <div py:if="build.getBuildType() != buildtypes.IMAGELESS" id="${build.getId()}_short" class="smallSpecs">
                                    ${build.getArch()} ${buildtypes.typeNamesShort[build.getBuildType()]} ${build.getDefaultName()}
                                </div>
                                <div py:if="build.getBuildType() == buildtypes.IMAGELESS" id="${build.getId()}_short" class="smallSpecs">
                                    ${buildtypes.typeNamesShort[build.getBuildType()]} ${build.getDefaultName()}
                                </div></a></td>
                            <td class="rel-checkbox">
                                <input class="relcheck" type="checkbox" name="buildIds" value="${build.getId()}" onclick="buttonStatus();"/></td>
                        </tr>
                        <tr py:attrs="{'class': rowStyle and 'odd' or 'even'}">
                            <td></td>
                            <td colspan="2">
                            <div id="div_${build.getId()}" style="display: none;">
                             
                                <table class="formgrouptable">
                                <tr>
                                    <td class="form-label"><b>Group:</b></td>
                                    <td width="100%">${build.getTroveName()}</td>
                                </tr>
                                <tr>
                                    <td class="form-label"><b>Version:</b></td>
                                    <td>${build.getTroveVersion()}</td>
                                </tr>
			                    <tr>
                                    <td class="form-label"><b>Flavor:</b></td>
                                    <td>${str(build.getTroveFlavor()).replace(',', ', ')}</td>
                                </tr>
    			                <tr>
                                    <td class="form-label"><b>Architecture:</b></td>
                                    <td>
                                       <div  py:if="build.getBuildType() != buildtypes.IMAGELESS" class="troveData">${build.getArch()}</div>
                                       <div  py:if="build.getBuildType() == buildtypes.IMAGELESS" class="troveData">N/A</div></td>
                                </tr>
    			                <tr>
                                    <td class="form-label"><b>Release Type:</b></td>
                                    <td>${buildtypes.typeNames[build.getBuildType()]}</td>
                                </tr>
    			                <tr>
                                    <td class="form-label"><b>Image Notes:</b></td>
                                    <td>${build.getDesc() and build.getDesc() or 'None'}</td>
                                </tr>
    			                </table><br/>
                            </div> 
                            </td>
                        </tr>
                        <?python rowStyle ^= 1 ?>
                    </div>
                        </table>
                </div>
            </div>

            <p class="p-button"><button id="submitButton" type="submit" py:attrs="{'disabled': not releaseId and 'disable' or None}">${releaseId and "Update" or "Create"} Release</button></p>
            <?python
                # hacktastic way of not passing a None through a request
                if not releaseId:
                    releaseId = 0
            ?>
            <input type="hidden" name="id" value="${releaseId}" />
            </form>
            <p py:if="not (availableBuilds or currentBuilds)" class="help">There are currently no available images associated with this ${projectText().lower()} that contain downloadable files. One or more available images that contain downloadable files are required to create a release.  Click <a href="${basePath}builds">here</a> to create a new image.</p>
            </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
        </div>
    </div>
    </body>
</html>
