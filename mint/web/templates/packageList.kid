<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Maintain Packages: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            
            <div id="innerpage">
                <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                
                <div id="right" class="side">
                    ${resourcePane()}
                </div>

                <div id="middle">
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title">Maintain Packages</div>
                
                    <p py:if="message" class="message" py:content="message"/>
                    
                    <h2>Available Packages</h2>

                    <?python
                    if currentVersion is not None:
                        vlist = [x for x in versions if x[0] == currentVersion][0]
                    else:
                        vlist = []
                    ?>
                    <div py:if="not pkgList">No packages available, <a href="newPackage">create</a> one. </div>
                    <div py:if="pkgList" py:strip="True">
                        <div py:for="version in sorted(currentVersion is None and pkgList.keys() or [vlist[3]])" class="mailingListButtons">

                            <div py:for="namespace in sorted(currentVersion is None and pkgList[version].keys() or [vlist[2]])"
                                py:strip="True">

                                <table class="package-list">
                                <tr>
                                    <td class="package-version-header" colspan="3">Version ${version} (${namespace})</td>
                                </tr>
                                <?python
                                try:
                                   troveList = pkgList[version][namespace]
                                except KeyError:
                                   troveList = {}
                                ?>
                                <tr py:if="not troveList">
                                    <td colspan="3">No packages available for this Product Version</td>
                                </tr>
                                
                                <div py:for="troveName in sorted(troveList.keys())" py:strip="True">
                                    <div py:if="not troveName.startswith('group-')" py:strip="True">
                                    <?python
                                    data = troveList[troveName]
                                    label = data['develStageLabel']
                                    prodVer = data['productDefinition']['version']
                                    namespace = data['productDefinition']['namespace']
                                    ?>
                                    <tr>
                                        <td class="package-detail" width="100%">${troveName.replace(':source','')}</td>
                                        <td class="package-detail"><a class="option" href="newUpload?name=${troveName}&amp;label=${label}&amp;prodVer=${prodVer}&amp;namespace=${namespace}">Update Archive</a></td>
                                        <td class="package-detail"><a class="option" href="maintainPackageInterview?name=${troveName}&amp;label=${label}&amp;prodVer=${prodVer}&amp;namespace=${namespace}">Update Details</a></td>
                                    </tr>
                                    </div>
                                </div>
                                </table>
                            </div>
                            <div py:if="troveList">
                                    <p class="help">Click the "Update Archive" button to upload and build a new archive.<br/>
                                    Click the "Update Details" button to review the package details and build the package.</p>
                            </div>
                        </div>
                    </div>
                    <h2>Other Packages</h2>
                    The packages listed above are those that were previously created using Package Creator.  
                    For other packages, you will need to use the normal 
                    <a href="http://wiki.rpath.com/wiki/Conary:Packaging">package maintenance</a> work flow.
                    
                </div><!--middle-->
                <br class="clear" />
                <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div><!--layout-->
    </body>
</html>
