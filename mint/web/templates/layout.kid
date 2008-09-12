<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
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
            <div id="top" style="margin-bottom:5px">
                <img id="topgradleft" src="${cfg.staticPath}/apps/mint/images/topgrad_left-small.png" alt="" />
                <img id="topgradright" src="${cfg.staticPath}/apps/mint/images/topgrad_right-small.png" alt="" />
                <div id="corpLogo">
                    <a href="http://${SITE}">
                        <img src="${cfg.staticPath}/apps/mint/images/corplogo-small.gif" width="40" height="49" alt="rPath Logo" />
                    </a>
                </div>
                <div id="prodLogo">
                    <a href="http://${SITE}">
                        <img py:if="cfg.rBuilderOnline" src="${cfg.staticPath}/apps/mint/images/prodlogo-rbo.gif" alt="rBuilder Online Logo" />
                        <img py:if="not cfg.rBuilderOnline" src="${cfg.staticPath}/apps/mint/images/prodlogo.gif" alt="rBuilder Logo" />
                    </a>
                </div>
                <div id="topRight">
                    <form action="http://${cfg.siteHost}${cfg.basePath}search" method="get" id="searchForm">
                        <div>
                            <label class="search" for="searchLabel">I'm looking for a...</label>
                            <input class="search" name="search" id="searchLabel" type="text" value="$searchTerms" />
                            <button class="img" id="searchSubmit" type="submit"><img src="${cfg.staticPath}/apps/mint/images/search.png" alt="Search" /></button><br />
                            <input id="typeProject" type="radio" name="type" value="${projectText().title()}s" py:attrs="{'checked': (searchType == projectText().title()+'s') and 'checked' or None}" />
                            <label for="typeProject">${projectText().title()}</label>
                            <input id="typePackage" type="radio" name="type" value="Packages" py:attrs="{'checked': (searchType == 'Packages') and 'checked' or None}" />
                            <label for="typePackage">Package</label>
                            <div py:strip="True" py:if="auth.admin">
                            <input id="typeUser" type="radio" name="type" value="Users" py:attrs="{'checked': (searchType == 'Users') and 'checked' or None}" />
                            <label for="typeUser">User</label>
                            </div>
                            <span id="browseText">&nbsp;&nbsp;&nbsp;Browse&nbsp;<a href="http://${cfg.siteHost}${cfg.basePath}search?search=&amp;type=${projectText().title()}s">${projectText().lower()}s</a><span py:strip="True" py:if="auth.admin">&nbsp;or&nbsp;<a href="http://${cfg.siteHost}${cfg.basePath}users">users</a></span></span>
                        </div>
                    </form>
                </div>
            </div>
            <div py:if="latestRssNews and not maintenance.getMaintenanceMode(cfg)==maintenance.LOCKED_MODE" id="rssnews">
                Latest ${self.cfg.productName} news:
                <a target="_blank" href="${latestRssNews['link']}">${latestRssNews['title']}</a><span class="newsAge" py:if="'age' in latestRssNews">&nbsp;(posted ${latestRssNews['age']})</span>
            </div>
            <div py:if="maintenance.getMaintenanceMode(cfg)==maintenance.LOCKED_MODE" id="maintmode">
                ${cfg.productName} is currently in maintenance mode.
                <a py:if="auth.admin" href="${cfg.basePath}admin/maintenance">Click here to enter the site administration menu.</a>
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
            ${layoutFooter()}
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
