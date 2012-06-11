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
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                
                <div id="right" class="side">
                    ${resourcePane()}
                </div>

                <div id="middle">
                    ${productVersionMenu()}
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>

                    <div class="page-title">Maintain Packages</div>
                
                    <p py:if="message" class="message" py:content="message"/>
                    
                    <h2>Available Packages</h2>

                    <div py:if="not pkgList">No packages available for this product version. Please
                        <a href="newPackage">create a package</a> or select a different version from the list above.</div>
                    <div py:if="pkgList">
                        <p>Click the "Update Archive" button to upload and build a new archive.
                        Click the "Update Details" button to review the package details and build the package.</p>
                        <table class="package-list">
                            <thead>
                                <tr>
                                    <td class="package-version-header" colspan="3">Version ${version} (${namespace})</td>
                                </tr>
                            </thead>
                            <tbody>
                                <tr py:for="troveName, data in sorted(pkgList.items())">
                                    <?python
                                        label = data['stageLabel']
                                        prodVer = data['productDefinition']['version']
                                        namespace = data['productDefinition']['namespace']
                                    ?>
                                    <td class="package-detail" width="90%">${troveName.replace(':source','')}</td>
                                    <td class="package-detail"><a class="option" href="newUpload?name=${troveName}&amp;label=${label}&amp;prodVer=${prodVer}&amp;namespace=${namespace}">&nbsp;Update Archive&nbsp;</a></td>
                                    <td class="package-detail"><a class="option" href="maintainPackageInterview?name=${troveName}&amp;label=${label}&amp;prodVer=${prodVer}&amp;namespace=${namespace}">&nbsp;Update Details&nbsp;</a></td>
                                </tr>
                            </tbody>
                        </table>
                        <h2>Other Packages</h2>
                        <p>The packages listed above are those that were previously created using Package Creator.
                        For other packages, you will need to use the normal 
                        <a href="http://wiki.rpath.com/wiki/Conary:Packaging">package maintenance</a> work flow.</p>
                    </div>
                </div><!--middle-->
                <br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div><!--layout-->
    </body>
</html>
