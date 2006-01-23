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
                            <img id="rpathLogo" src="http://www.rpath.com/conary-static/apps/mint/images/corplogo.gif" alt="rPath Logo" />
                            <img id="logo" src="http://www.rpath.com/conary-static/apps/mint/images/prodlogo.gif" alt="rBuilder Online Logo" />
                        </td>
                        <td id="topRight">
                            <div class="about">About rPath</div>
                            <table style="width: 100%;" class="search">
                                <tr>
                                    <td>I'm looking for a...</td>
                                    <td><input style="width: 100%;" type="text" /></td>
                                    <td style="text-align: right;"><img src="${cfg.staticPath}/apps/mint/images/search.png" alt="Search" /></td>
                                </tr>
                                <tr>
                                    <td></td>
                                    <td style="vertical-align: middle;"><input type="radio" /> Project <input type="radio" /> Package</td>
                                    <td style="text-align: right;">Or you can <a href="projects">browse</a>.</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </div>

            <div class="layout" py:replace="item[:]" />

            <div id="footer">
                <div>
                    <span style="float: right"><a href="#top">Top of Page</a></span>
                    <ul class="footerLinks">
                        <li>About rPath</li>
                        <li>Site Announcements</li>
                        <li>Legal</li>
                        <li>Contact Us</li>
                        <li>Help</li>
                    </ul>
                </div>
                <div style="border-top: 1px solid #c4c4c4; padding: 6px;">
                    <span id="copyright">Copyright &copy; 2005-2006 rPath. All Rights Reserved.</span>
                    <span id="tagline">rPath. The Software Appliance Company.</span>
                </div>
            </div>
        </div>
    </body>
</html>
