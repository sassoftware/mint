<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright 2005 rPath, Inc.
# All Rights Reserved
#
from mint import userlevels
from mint import constants
from urllib import quote
onload = "javascript:;"
?>

<html xmlns:py="http://purl.org/kid/ns#"
      py:extends="'project.kid', 'library.kid'">
    <div py:def="breadcrumb()" class="pad" py:strip="True">
    </div>

    <div py:def="topnav()" py:strip="True">
        <td id="topnav">
            <div class="pad">
                <a href="http://$SITE">Home</a> | 
                <a py:if="False" href="${cfg.corpSite}">About rPath</a>
                <a py:if="False" href="${cfg.corpSite}sales/">Contact rPath</a>
                <a href="http://${SITE}help?page=feedback"><b style="color: red;">Need Help/Have Feedback?</b></a>
                <span py:if="cfg.debugMode">
                    | <span style="color:red;">DEBUG MODE</span>
                </span>
            </div>
        </td>
    </div>


    <div py:def="rPathProductsMenu" id="products" class="palette" py:if="False">
        <h3>rPath products</h3>
        <ul>
            <li><a href="#">Product 1</a></li>
            <li><a href="#">Product 2</a></li>
            <li>Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras erat. Curabitur tempus nulla sit amet justo. Morbi quis tellus sed turpis bibendum egestas. Phasellus nonummy!</li>
        </ul>
    </div>

    <head py:match="item.tag == 'head'" xmlns="http://www.w3.org/1999/xhtml">
        <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/generic.js"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/library.js"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/xmlrpc.js"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/basic.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/structure.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/user.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/topNav.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/log.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/contentTypes.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/mint.css"/>

        <link rel="shortcut icon" href="http://www.rpath.com/favicon.ico" />
        <link rel="icon" href="http://www.rpath.com/favicon.ico" />
        <div py:replace="item[:]"/>
    </head>
    <body xmlns="http://www.w3.org/1999/xhtml"
          py:match="item.tag == 'body'"
          py:attrs="item.attrib"> 
        <img style="display: none;"
             src="http://${cfg.siteHost}${cfg.basePath}blank?sid=${session.id()};hostname=.${cfg.siteDomainName}" width="1" height="1" />
        <img style="display: none;"
             src="http://${cfg.projectSiteHost}${cfg.basePath}blank?sid=${session.id()};hostname=.${cfg.projectDomainName}" width="1" height="1" />

        <div id="top" align="center">
            <div class="shadowLeft"><div class="shadowRight">
                <div class="surfaceLeft" align="left"><div class="surfaceRight">
                    ${userActions()}
                </div></div>
            </div></div>
        </div>
        <div id="middle" align="center">
            <div id="crumb">
                <div class="pad">
                    You are here: <a href="http://$SITE">Home</a>
                    ${breadcrumb()}
                </div>
            </div>
        </div>
        <div id="bottom" align="center">
            <div class="shadowLeft"><div class="shadowRight">
                <div class="surfaceLeft" align="left"><div class="surfaceRight">
                    <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                        <tr>
                            <td id="main" class="spanleft" py:replace="item[:]" />
                        </tr>
                    </table>
                </div></div>
            </div></div>
        </div>
        <div id="foot" align="center">
            <div id="copy">
                <div class="pad" style="text-align: center;">
                    <span id="botnav">
                        ${legal('http://%slegal?page=legal' % SITE, 'Legal')}
                    </span>

                    <span style="float: left;">Copyright &#169; 2005 rPath, Inc. </span>

                    <span>version ${constants.mintVersion}</span>
                </div> 
            </div>
        </div>
    </body>
</html>
