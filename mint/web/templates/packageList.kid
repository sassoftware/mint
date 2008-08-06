<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
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
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="middle">
              <p py:if="message" class="message" py:content="message"/>
              <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
              <h2>Package Creator - Available Packages</h2>

              <?python
              if currentVersion is not None:
                vlist = [x for x in versions if x[0] == currentVersion][0]
              else:
                vlist = []
              ?>
              <div py:if="not pkgList">No packages available, <a href="newPackage">create</a> one. </div>
              <div py:if="pkgList" py:strip="True">
                <div py:for="version in sorted(currentVersion is None and pkgList.keys() or [vlist[3]])" class="mailingListButtons">

                  <div py:for="namespace in sorted(currentVersion is None and pkgList[version].keys() or [vlist[2]])" py:strip="True">
                    <h3>Product Version ${version} (${namespace})</h3>

                    <?python
                    try:
                        troveList = pkgList[version][namespace]
                    except KeyError:
                        troveList = {}
                    ?>
                    <h4 py:if="not troveList">No packages available for this Product Version</h4>
                    <div py:for="troveName in sorted(troveList.keys())" py:strip="True">
                      <div py:if="not troveName.startswith('group-')" py:strip="True">
                        <?python
                        data = troveList[troveName]
                        label = data['develStageLabel']
                        prodVer = data['productDefinition']['version']
                        namespace = data['productDefinition']['namespace']
                        ?>
                        <h4>${troveName.replace(':source','')}</h4>
                        <ul>
                          <li>
                            <a class="option" href="newUpload?name=${troveName}&amp;label=${label}&amp;prodVer=${prodVer}&amp;namespace=${namespace}">Update Archive</a>
                            <a class="option" href="maintainPackageInterview?name=${troveName}&amp;label=${label}&amp;prodVer=${prodVer}&amp;namespace=${namespace}">Update Details</a>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <h3 style="color:#FF7001;">Select which package you would like to maintain</h3>
              <p>The packages listed above are those that were previously
              created using Package Creator.  For other packages, you will need
              to use the normal <a href="http://wiki.rpath.com/wiki/Conary:Packaging">package maintenance</a> work flow.</p>
              <p>Click the "Update Archive" button to provide a new archive and build it.</p>
              <p>Click the "Update Details" button to review the package details, and build the package.</p>
            </div><!--middle-->
        </div><!--layout-->
    </body>
</html>
