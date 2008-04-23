<?xml version='1.0' encoding='UTF-8'?>
<?python
from urllib import quote
from conary.deps import deps
from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>Find References</title>
    </head>

    <body>
        <div id="layout">
            <div id="right" class="side">
                ${projectsPane()}
            </div>
            <div id="spanleft">
                <h1>References and Descendants</h1>


                <ul py:def="referenceList(refList)" class="referenceList">
                    <li py:for="project, refs in refList.items()">
                        <a href="${project.getUrl()}">${project.getName()}</a>
                        <ul>
                            <li py:for="ref in refs">
                                <a href="${cfg.basePath}repos/${project.hostname}/troveInfo?t=${quote(ref[0])};v=${quote(ref[1])}">
                                    <span py:omit="True" py:if="ref[0] != trvName">${ref[0]}=</span>${ref[1]}
                                </a>
                            </li>
                        </ul>
                    </li>
                    <li py:if="not refList" style="font-size: smaller; font-weight: normal;">
                        No references found.
                    </li>
                </ul>

                <h4>The following ${projectText().lower()}s have groups that contain $trvName=$trvVersion:</h4>
                ${referenceList(references)}

                <h4>The following ${projectText().lower()}s have derived from $trvName=$trvVersion:</h4>
                ${referenceList(descendants)}

            </div>
        </div>
    </body>
</html>
