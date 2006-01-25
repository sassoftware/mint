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
        <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8" />
        <meta name="KEYWORDS" content="rPath, rBuilder, rBuilder Online, rManager, rPath Linux, rPl, Conary, Software Appliance, Application image, Software as a Service, SaaS, Virtualization, virtualisation, open source, Linux," />
        <meta name="DESCRIPTION" content="rPath enables applications to be delivered as a software appliance which combines a software application and a streamlined version of system software that easily installs on industry standard hardware (typically a Linux server)." />

        <script type="text/javascript" src="${cfg.staticPath}apps/MochiKit/MochiKit.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/generic.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/library.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/xmlrpc.js" />
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
                <table style="width: 95%;">
                    <tr>
                        <td style="width: 50%;">
                            <div id="corpLogo">
                                <a href="http://${SITE}">
                                    <img src="${cfg.staticPath}/apps/mint/images/corplogo.png" width="78" height="94" alt="rPath Logo" />
                                </a>
                            </div>
                            <div id="prodLogo">
                                <a href="http://${SITE}">
                                    <img src="${cfg.staticPath}/apps/mint/images/prodlogo.gif" alt="rBuilder Online Logo" />
                                </a>
                            </div>
                        </td>
                        <td id="topRight">
                            <div class="about"><a href="http://www.rpath.com/corp/about/">About rPath</a></div>
                            <form action="http://${cfg.siteHost}${cfg.basePath}search" method="get" id="searchForm">
                                <table style="width: 100%;" class="search">
                                    <tr>
                                        <td>I'm looking for a...</td>
                                        <td><input style="width: 100%;" type="text" name="search" /></td>
                                        <td style="text-align: right;">
                                            <button id="searchSubmit" type="submit"><img src="${cfg.staticPath}/apps/mint/images/search.png" alt="Search" /></button>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td></td>
                                        <td style="vertical-align: middle;">
                                            <input type="radio" name="type" value="Projects" checked="checked" /> Project
                                            <input type="radio" name="type" value="Packages" /> Package</td>
                                        <td style="text-align: right;">Or you can <a href="http://${cfg.siteHost}${cfg.basePath}projects">browse</a>.</td>
                                    </tr>
                                </table>
                            </form>
                        </td>
                    </tr>
                </table>
            </div>

            <div class="layout" py:replace="item[:]" />

            <div id="footer">
                <div>
                    <span id="topOfPage"><a href="#top">Top of Page</a></span>
                    <ul class="footerLinks">
                        <li><a href="/corp/about/">About rPath</a></li>
                        <li><a href="/news/">Site Announcements</a></li>
                        <li><a href="/legal/">Legal</a></li>
                        <li><a href="/contact/">Contact Us</a></li>
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
