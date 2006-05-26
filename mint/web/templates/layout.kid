<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
from mint import constants
from mint import maintenance
from mint import userlevels
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
                    <div class="about">
                        <a href="${cfg.basePath}admin/maintenance" py:if="auth.admin and maintenance.getMaintenanceMode(cfg)==maintenance.LOCKED_MODE">
                          <b style="color: red;">
                          Maintenance Mode&nbsp;
                          </b>
                        </a>
                        <a href="${cfg.corpSite}">About ${cfg.companyName}</a>
                        <span py:omit="True" py:if="not auth.authorized and req.uri != cfg.basePath"> | <a href="http://${SITE}">Sign In</a></span>
                    </div>
                    <form action="http://${cfg.siteHost}${cfg.basePath}search" method="get" id="searchForm">
                        <div>
                            <label class="search" for="searchLabel">I'm looking for a...</label>
                            <input class="search" name="search" id="searchLabel" type="text" />
                            <button class="img" id="searchSubmit" type="submit"><img src="${cfg.staticPath}/apps/mint/images/search.png" alt="Search" /></button><br />
                            <input id="typeProject" type="radio" name="type" value="Projects" py:attrs="{'checked': self.session.get('searchType', 'Projects') == 'Projects' and 'checked' or None}" />
                            <label for="typeProject">Project</label>
                            <input id="typePackage" type="radio" name="type" value="Packages" py:attrs="{'checked': self.session.get('searchType', 'Projects') == 'Packages' and 'checked' or None}" />
                            <label for="typePackage">Package</label>
                            <div py:strip="True" py:if="auth.admin">
                            <input id="typeUser" type="radio" name="type" value="Users" py:attrs="{'checked': self.session.get('searchType', 'Projects') == 'Users' and 'checked' or None}" />
                            <label for="typeUser">User</label>
                            </div>
                            <span id="browseText">&nbsp;&nbsp;&nbsp;Browse&nbsp;<a href="http://${cfg.siteHost}${cfg.basePath}projects">projects</a><span py:strip="True" py:if="auth.admin">&nbsp;or&nbsp;<a href="http://${cfg.siteHost}${cfg.basePath}users">users</a></span></span>
                        </div>
                    </form>
                </div>
            </div>
            <?python
                if 'errors' in locals():
                    errorMsgList = errors
            ?>
            <div py:if="infoMsg" id="info" class="status" py:content="infoMsg" />
            <div py:if="errorMsgList" id="errors" class="status">The following ${(len(errorMsgList) == 1) and "error" or "errors"} occurred:
                <p py:for="e in errorMsgList" py:content="e" />
            </div>
            <div id="layout" py:replace="item[:]" />
            <div id="footer">
                <div>
                    <span id="topOfPage"><a href="#top">Top of Page</a></span>
                    <ul class="footerLinks">
                        <li><a href="${cfg.corpSite}">About ${cfg.companyName}</a></li>
                        <li py:if="cfg.announceLink"><a href="${cfg.announceLink}">Site Announcements</a></li>
                        <li><a href="${cfg.basePath}legal/">Legal</a></li>
                        <li><a href="${cfg.corpSite}company-contact-rpath.html">Contact Us</a></li>
                        <li><a href="${cfg.basePath}help/">Help</a></li>
                    </ul>
                </div>
                <div id="bottomText">
                    <span id="copyright">Copyright &copy; 2005-2006 rPath. All Rights Reserved.</span>
                    <span id="tagline">rPath. The Software Appliance Company.</span>
                </div>

                <p id="mintVersionString">${cfg.productName} version ${constants.mintVersion}</p>
            </div>
        </div>
        <div py:if="cfg.googleAnalyticsTracker" py:strip="True">
<script src="http://www.google-analytics.com/urchin.js" type="text/javascript">
</script>
<script type="text/javascript">
_uacct = "UA-284172-1";
urchinTracker();
</script>
        </div>
    </body>
</html>
