<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
from mint import userlevels
from mint import constants
from urllib import quote
onload = "javascript:;"
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'project.kid', 'library.kid'">
    <head py:match="item.tag == '{http://www.w3.org/1999/xhtml}head'" >
        <meta name="KEYWORDS" content="rPath, rBuilder, rBuilder Online, rManager, rPath Linux, rPl, Conary, Software Appliance, Application image, Software as a Service, SaaS, Virtualization, virtualisation, open source, Linux," />
        <meta name="DESCRIPTION" content="rPath enables applications to be delivered as a software appliance which combines a software application and a streamlined version of system software that easily installs on industry standard hardware (typically a Linux server)." />

        <script type="text/javascript" src="${cfg.staticPath}apps/MochiKit/MochiKit.js" />
        <script type="text/javascript">
            <![CDATA[
                var BaseUrl = '${cfg.basePath}';

                // Configured visible image types; required for library.js
                var VisibleImageTypes = ${str(cfg.visibleImageTypes)};
                var VisibleBootableImageTypes = ${str([x for x in (3, 4, 5, 6, 7, 8) if x in cfg.visibleImageTypes])};
            ]]>
        </script>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/generic.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/releasetypes.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/jobstatus.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/library.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/rpc.js" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/mint.css" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/search.css" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/help.css" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/contentTypes.css" />

        <link rel="shortcut icon" href="http://www.rpath.com/favicon.ico" />
        <link rel="icon" href="http://www.rpath.com/favicon.ico" />
        <div py:replace="item[:]"/>
    </head>

    <body py:match="item.tag == '{http://www.w3.org/1999/xhtml}body'"
          py:attrs="item.attrib">
        <div id="main">
            <a name="top" />
            <div id="top">
                <img id="topgradleft" src="${cfg.staticPath}/apps/mint/images/topgrad_left.png" alt="" />
                <img id="topgradright" src="${cfg.staticPath}/apps/mint/images/topgrad_right.png" alt="" />
                <div id="corpLogo">
                    <a href="http://${SITE}">
                        <img src="${cfg.staticPath}/apps/mint/images/corplogo_notrans.png" width="80" height="98" alt="rPath Logo" />
                    </a>
                </div>
                <div id="prodLogo">
                    <a href="http://${SITE}">
                        <img src="${cfg.staticPath}/apps/mint/images/prodlogo.gif" alt="rBuilder Online Logo" />
                    </a>
                </div>
                <div id="topRight">
                    <div class="about"><a href="${cfg.corpSite}">About ${cfg.companyName}</a>
                        <span py:omit="True" py:if="not auth.authorized and req.uri != cfg.basePath"> | <a href="http://${SITE}">Sign In</a></span>
                    </div>
                    <form action="http://${cfg.siteHost}${cfg.basePath}search" method="get" id="searchForm">
                        <div>
                            <label class="search" for="searchLabel">I'm looking for a...</label>
                            <input class="search" name="search" id="searchLabel" type="text" />
                            <button class="img" id="searchSubmit" type="submit"><img src="${cfg.staticPath}/apps/mint/images/search.png" alt="Search" /></button><br />
                            <input id="typeProject" type="radio" name="type" value="Projects" checked="checked" />
                            <label for="typeProject">Project</label>
                            <input id="typePackage" type="radio" name="type" value="Packages" />
                            <label for="typePackage">Package</label>
                            <span id="browseText">&nbsp;&nbsp;&nbsp;Or you can <a href="http://${cfg.siteHost}${cfg.basePath}projects">browse</a>.</span>
                        </div>
                    </form>
                </div>
            </div>
            <div class="layout" py:replace="item[:]" />

            <div id="footer">
                <div>
                    <span id="topOfPage"><a href="#top">Top of Page</a></span>
                    <ul class="footerLinks">
                        <li><a href="${cfg.corpSite}">About ${cfg.companyName}</a></li>
                        <li py:if="cfg.announceLink"><a href="${cfg.announceLink}">Site Announcements</a></li>
                        <li><a href="/help/">Help</a></li>
                    </ul>
                </div>
                <div id="bottomText">
                    <span id="copyright">Copyright &copy; 2005-2006 rPath. All Rights Reserved.</span>
                    <span id="tagline">rPath. The Software Appliance Company.</span>
                </div>
            </div>
        </div>
    </body>
</html>
