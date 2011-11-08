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
      py:extends="'library.kid'">
    <head py:match="item.tag == '{http://www.w3.org/1999/xhtml}head'" >
        <meta name="KEYWORDS" content="rPath, rBuilder, rBuilder Online, rManager, rPath Linux, rPl, Conary, Software Appliance, Application image, Software as a Service, SaaS, Virtualization, virtualisation, open source, Linux," />
        <meta name="DESCRIPTION" content="rPath enables applications to be delivered as a software appliance which combines a software application and a streamlined version of system software that easily installs on industry standard hardware (typically a Linux server)." />

        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/jquery-1.2.6.min.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/jquery.ui-1.5.2.all.min.js?v=${cacheFakeoutVersion}" />
        <!--[if lte IE 6.5]><script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/jquery.bgiframe.min.js?v=${cacheFakeoutVersion}"></script><![endif]-->
        <script type="text/javascript">
            <![CDATA[
                jQuery.noConflict();
                var BaseUrl = '${cfg.basePath}';
                var staticPath = "${cfg.staticPath}";

                /* fade out info messages after 5s */
                jQuery(document).ready(function() {
                    jQuery('#info')
                        .animate({'opacity': 1}, 5000)
                        .fadeOut('slow');
                });

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
        <a name="top" />
        <div id="main">
            <div id="top">
                <img id="topgradleft" src="${cfg.staticPath}/apps/mint/images/topgrad_left.png" alt="" />
                <img id="topgradright" src="${cfg.staticPath}/apps/mint/images/topgrad_right.png" alt="" />
                <div id="corpLogo">
                    <a href="http://${SITE}">
                        <img src="${cfg.staticPath}/apps/mint/images/corplogo.png" alt="rPath Logo" />
                    </a>
                </div>
                <div id="prodLogo">
                    <a href="http://${SITE}">
                        <img py:if="cfg.rBuilderOnline" src="${cfg.staticPath}/apps/mint/images/prodlogo-rbo.png" alt="rBuilder Online Logo" />
                        <img py:if="not cfg.rBuilderOnline" src="${cfg.staticPath}/apps/mint/images/prodlogo.png" alt="rBuilder Logo" />
                    </a>
                </div>
                <div id="topRight">
                    <form action="${cfg.basePath}search" method="get" id="searchForm">
                        <div class="searchParams">
                            <label class="search"><strong>SEARCH</strong> for a...</label>
                            <input id="typeProject" type="radio" name="type" value="${projectText().title()}s" py:attrs="{'checked': (searchType == projectText().title()+'s') and 'checked' or None}" />
                            <label for="typeProject"><strong>${projectText().title()}</strong></label>
                            <input id="typePackage" type="radio" name="type" value="Packages" py:attrs="{'checked': (searchType == 'Packages') and 'checked' or None}" />
                            <label for="typePackage"><strong>Package</strong></label>
                            <div py:strip="True" py:if="auth.admin">
                            <input id="typeUser" type="radio" name="type" value="Users" py:attrs="{'checked': (searchType == 'Users') and 'checked' or None}" />
                            <label for="typeUser"><strong>User</strong></label>
                            </div><br/>
                            <button class="img" id="searchSubmit" type="submit"><img src="${cfg.staticPath}/apps/mint/images/search.png" alt="Search" /></button>
                            <input class="searchField" name="search" id="searchLabel" type="text" value="$searchTerms" /><br/>
                            <div id="browseText">
                                <strong>BROWSE</strong> ... &nbsp;&nbsp;<a href="${cfg.basePath}search?search=&amp;type=${projectText().title()}s"><strong>${projectText().capitalize()}s</strong></a><span py:strip="True" py:if="auth.admin">,&nbsp;<a href="${cfg.basePath}users"><strong>Users</strong></a>,</span><span py:strip="True" py:if="auth.authorized">&nbsp;or&nbsp;<a target="_blank" href="https://${SITE}cloudCatalog/"><strong>rPath Management Console</strong></a></span>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            <div py:if="maintenance.getMaintenanceMode(cfg)==maintenance.LOCKED_MODE" id="maintmode">
                <p>${cfg.productName} is currently in maintenance mode.
                <a py:if="auth.admin" href="${cfg.basePath}admin/maintenance">Click here to enter the site administration menu.</a>
                </p>
            </div>
            <?python
                if 'errors' in locals():
                    errorMsgList = errors
            ?>
            <div py:if="infoMsg" id="info" class="status" py:content="infoMsg" />
            <div py:if="errorMsgList" id="errors" class="status"><strong>The following ${(len(errorMsgList) == 1) and "error" or "errors"} occurred:</strong>
                <p py:for="e in errorMsgList" py:content="e" />
            </div>
            <div id="page">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/page_topleft.gif" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/page_topright.gif" alt="" />
                <div id="layout" py:replace="item[:]" />
                ${layoutFooter()}<br />
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
