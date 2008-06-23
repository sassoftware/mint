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
              <h1>Package Creator - Available Packages</h1>

              <div py:for="pkgs in pkgList" class="mailingListButtons">
                <h3>${pkgs[0].replace(':source','')}</h3>
                <ul>
                  <li>
                    <a class="option" href="newUpload?name=${pkgs[0]}&amp;label=${pkgs[1]}">new archive</a>
                    <a class="option" href="maintainPackageInterview?name=${pkgs[0]}&amp;label=${pkgs[1]}">edit data</a>
                  </li>
                </ul>
              </div>
              <h3 style="color:#FF7001;">Select which package you would like to maintain</h3>
              <p>Blah blah blah</p>
            </div><!--middle-->
        </div><!--layout-->
    </body>
</html>
