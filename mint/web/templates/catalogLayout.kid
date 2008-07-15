<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint import constants
from mint import maintenance
from mint import helperfuncs
from mint.web.templatesupport import projectText

from urllib import quote
onload = "javascript:;"
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'project.kid', 'library.kid'">
    <head py:match="item.tag == '{http://www.w3.org/1999/xhtml}head'" >
        <meta name="KEYWORDS" content="rPath, rBuilder, rBuilder Online, rManager, rPath Linux, rPl, Conary, Software Appliance, Application image, Software as a Service, SaaS, Virtualization, virtualisation, open source, Linux," />
        <meta name="DESCRIPTION" content="rPath enables applications to be delivered as a software appliance which combines a software application and a streamlined version of system software that easily installs on industry standard hardware (typically a Linux server)." />

        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/jquery-1.2.6.min.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/jquery.ui-1.5.2.all.min.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript">
            <![CDATA[
                jQuery.noConflict();
                var BaseUrl = '${cfg.basePath}';
                var x86_64 = ${int(cfg.bootableX8664)};
                var staticPath = "${cfg.staticPath}";
            ]]>
        </script>
        <script type="text/javascript" src="${cfg.staticPath}apps/MochiKit/MochiKit.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/buildtypes.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/jobstatus.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/library.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/rpc.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/dialogs.js?v=${cacheFakeoutVersion}"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/mint.css?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/search.css?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/help.css?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/contentTypes.css?v=${cacheFakeoutVersion}" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/dialogs.css?v=${cacheFakeoutVersion}" />

        <link rel="shortcut icon" href="${cfg.staticPath}apps/mint/images/favicon.ico" />
        <link rel="icon" href="${cfg.staticPath}apps/mint/images/favicon.ico" />
        <div py:replace="item[:]"/>
    </head>

    <body py:match="item.tag == '{http://www.w3.org/1999/xhtml}body'"
          py:attrs="item.attrib">
        <div py:if="bulletin" id="bulletin">${XML(bulletin)}</div>
        <div id="main">
            <a name="top" />
            <div id="top" style="background:
               url('${cfg.staticPath}/apps/mint/images/topgrad-small.png'); height: 72px">
                <img id="topgradleft" src="${cfg.staticPath}/apps/mint/images/topgrad_left-small.png" alt="" />
                <img id="topgradright" src="${cfg.staticPath}/apps/mint/images/topgrad_right-small.png" alt="" />
                <div id="corpLogo">
                    <a href="http://${SITE}">
                        <img src="${cfg.staticPath}/apps/mint/images/corplogo-small.gif" width="40" height="49" alt="rPath Logo" />
                    </a>
                </div>
                <div id="prodLogo" style="margin-top: 14px;">
                    <a href="http://${SITE}">
                        <img src="${cfg.staticPath}/apps/mint/images/catalog-logo.png" alt="rBuilder catalog" />
                    </a>
                </div>
            </div>
            <?python
                if 'errors' in locals():
                    errorMsgList = errors
            ?>
            <div py:if="inlineMime">
                <?python
                    mime, mimeArgs = inlineMime
                ?>
                <frame src="${mime}?${':'.join([x[0] + '=' + x[1] for x in mimeArgs])}" name="inlineMime" id="inlineMime">
                    <script type="text/javascript">
                        <![CDATA[
                            addLoadEvent(function() {
                              window.location.replace(document.URL);});
                        ]]>
                    </script>
                </frame>
            </div>
            <div py:if="infoMsg" id="info" class="status" py:content="infoMsg" />
            <div py:if="errorMsgList" id="errors" class="status">The following ${(len(errorMsgList) == 1) and "error" or "errors"} occurred:
                <p py:for="e in errorMsgList" py:content="e" />
            </div>
            <div id="layout" py:replace="item[:]" />
            <div id="footer">
                <div>
                    <span id="topOfPage"><a href="#top">Top of Page</a></span>
                    <ul class="footerLinks">
                        <li py:if="cfg.rBuilderOnline"><a href="${cfg.corpSite}">About ${cfg.companyName}</a></li>
                        <li py:if="cfg.announceLink"><a href="${cfg.announceLink}">Site Announcements</a></li>
                        <li py:if="cfg.legaleseLink"><a href="${cfg.legaleseLink}">Legal</a></li>
                        <li py:if="cfg.rBuilderOnline"><a href="${cfg.corpSite}company-contact-rpath.html">Contact Us</a></li>
                        <li><a href="http://wiki.rpath.com/wiki/rBuilder?version=${constants.mintVersion}" target="_blank">rBuilder ${constants.mintVersion} User Guide</a></li>
                        <li py:if="auth.admin"><a href="http://wiki.rpath.com/wiki/rBuilder:Administration_Guide?version=${constants.mintVersion}" target="_blank">rBuilder ${constants.mintVersion} Administration Guide</a></li>
                    </ul>
                </div>
                <div id="bottomText">
                    <span id="copyright">Copyright &copy; 2005-2008 rPath. All Rights Reserved.</span>
                    <span id="tagline">rPath. The Software Appliance Company.</span>
                </div>
                <!-- ${cfg.productName} version ${constants.fullVersion} -->
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
