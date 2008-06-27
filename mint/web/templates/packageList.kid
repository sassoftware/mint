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

              <div py:for="version in sorted(pkgList.keys())" class="mailingListButtons">

                <div py:for="namespace in sorted(pkgList[version].keys())" py:strip="True">
                  <h3 py:if="len(pkgList[version]) == 1">Product Version ${version}</h3>
                  <h3 py:if="len(pkgList[version]) != 1">Product Version ${version} (${namespace})</h3>

                  <?python
                  troveList = pkgList[version][namespace]
                  ?>
                  <!--
{u'1': {'zope:s  ource': {u'develStageLabel': u'foo.rdu.rpath.com@f:foo-1-devel',
    u'productDe  finition': {u'hostname': u'foo.rdu.rpath.com',
    u'namespace  ': u'f',
    u'shortname  ': u'foo',
    u'version':   u'1'}}}}
    -->
                  <div py:for="troveName in sorted(troveList.keys())" py:strip="True">
                    <?python
                    data = troveList[troveName]
                    label = data['develStageLabel']
                    prodVer = data['productDefinition']['version']
                    namespace = data['productDefinition']['namespace']
                    ?>
                    <h4>${troveName.replace(':source','')}</h4>
                    <ul>
                      <li>
                        <a class="option" href="newUpload?name=${troveName}&amp;label=${label}&amp;prodVer=${prodVer}&amp;namespace=${namespace}">new archive</a>
                        <a class="option" href="maintainPackageInterview?name=${troveName}&amp;label=${label}&amp;prodVer=${prodVer}&amp;namespace=${namespace}">edit data</a>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
              <h3 style="color:#FF7001;">Select which package you would like to maintain</h3>
              <p>The packages listed above are those that were previously
              created using Package Creator.  For other packages, you will need
              to use the normal <a href="http://wiki.rpath.com/wiki/Conary:Packaging">package maintenance</a> work flow.</p>
            </div><!--middle-->
        </div><!--layout-->
    </body>
</html>
