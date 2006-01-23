<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import userlevels
from mint import searcher
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Front Page')}</title>
        <link py:if="cfg.newsRssFeed" rel="alternate" type="application/rss+xml"
              title="${cfg.productName} Site Announcements" href="${cfg.newsRssFeed}" />
        <link rel="alternate" type="application/rss+xml"
              title="New ${cfg.productName} Projects" href="http://${cfg.siteHost}${cfg.basePath}rss?feed=newProjects" />
        <link rel="alternate" type="application/rss+xml"
              title="New ${cfg.productName} ISO Releases" href="http://${cfg.siteHost}${cfg.basePath}rss?feed=newReleases" />
    </head>
    <body>
        <div id="steps">
            <span id="signin" py:if="not auth.authorized">
                <?python
                    from urllib import quote
                    secureProtocol = 'http'
                    if auth.authorized:
                        loginAction = "logout"
                    else:
                        loginAction = "processLogin"
                    if cfg.SSL:
                        secureProtocol = "https"
                ?>
                <form method="post" action="${secureProtocol}://${cfg.secureHost}${cfg.basePath}processLogin">
                    <input type="hidden" name="to" value="${quote(toUrl)}" />

                    <div>Username:</div>
                    <div><input type="text" name="username" /></div>
                    <div style="padding-top: 8px;">Password:</div>
                    <div><input type="password" name="password" /></div>
                    <div style="padding-top: 8px;">
                        <input type="checkbox" name="remember_me" />
                        <u>Remember me</u> on this computer
                    </div>
                    <input type="image" id="sign_in_button" src="${cfg.staticPath}apps/mint/images/sign_in_button.png" width="94" height="31" />

                    <div style="border-top: 2px dotted gray;">
                        <p>Don't have an account?</p>
                        <p><a href="register">Set one up.</a></p>
                    </div>
                </form>
            </span>
            <span id="buildit">Find the stuff you need to make your own software appliance in three easy steps.</span>
            <span id="findit">Check out all the amazing software applications others have made.</span>

            <img style="clear: left;" src="${cfg.staticPath}apps/mint/images/steps.png" />
        </div>

        <div id="topten">
            <table style="width: 100%;">
                <tr>
                    <td><img src="${cfg.staticPath}apps/mint/images/rss.png" /><span class="topten_header">Most Popular</span>
                        <ol>
                            <li py:for="project in popularProjects">
                                <a href="http://${cfg.projectSiteHost}${cfg.basePath}/project/${project[1]}/">${project[2]}</a>
                            </li>
                        </ol>
                    </td>
                    <td><img src="${cfg.staticPath}apps/mint/images/rss.png" /><span class="topten_header">Most Active</span>
                        <ol>
                            <li py:for="project in activeProjects">
                                <a href="http://${cfg.projectSiteHost}${cfg.basePath}/project/${project[1]}/">${project[2]}</a>
                            </li>
                        </ol>
                    </td>
                    <td><img src="${cfg.staticPath}apps/mint/images/rss.png" /><span class="topten_header">Recent Updates</span>
                        <ol>

                            <li py:for="release in releases">
                                <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${release[1]}/release?id=${release[2].getId()}">${release[2].getTroveName()}=${release[2].getTroveVersion().trailingRevision().asString()} (${release[2].getArch()})</a>
                            </li>
                        </ol>
                    </td>
                </tr>
            </table>
        </div>
    </body>
</html>
