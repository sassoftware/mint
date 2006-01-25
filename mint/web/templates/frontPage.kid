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
            <form py:if="not auth.authorized" method="post" action="${secureProtocol}://${cfg.secureHost}${cfg.basePath}processLogin">
                <div id="signin" py:if="not auth.authorized">
                    <input type="hidden" name="to" value="${quote(toUrl)}" />

                    <div>Username:</div>
                    <div><input type="text" name="username" /></div>
                    <div style="padding-top: 8px;">Password:</div>
                    <div><input type="password" name="password" /></div>
                    <div style="padding-top: 8px;">
                        <input type="checkbox" name="remember_me" value="1" />
                        <u>Remember me</u> on this computer
                    </div>
                    <button id="signInSubmit" type="submit">
                        <img alt="Sign In" src="${cfg.staticPath}apps/mint/images/sign_in_button.png" />
                    </button>

                    <div id="noAccount">
                        <p><strong>Don't have an account?</strong></p>
                        <p><a href="register">Set one up.</a></p>
                    </div>
                </div>
            </form>
            <div id="signedIn" py:if="auth.authorized">
                You are signed in as ${auth.username}.
                <p><a href="http://${cfg.siteHost}${cfg.basePath}logout">Sign Out</a></p>
            </div>
            <span id="buildit">Find the stuff you need to make your own software appliance in three easy steps.</span>
            <span id="findit">Check out all the amazing software applications others have made.</span>

            <div id="threeEasySteps">
                <a href="/help?page=dev-tutorial">
                    <img id="getStarted" src="${cfg.staticPath}apps/mint/images/getting_started.png" width="147" height="37" alt="Get Started" />
                </a>
                <img src="${cfg.staticPath}apps/mint/images/three_easy_steps.png" width="239" height="23" alt="It's Just 3 Easy Steps" />
                <div id="stepsText">There's nothing to download. All you need is your web browser.</div>
                <img style="clear: left;" src="${cfg.staticPath}apps/mint/images/steps.png" alt="three steps to use rBuilder Online" />
            </div>
        </div>

        <div id="topten">
            <table style="width: 100%;">
                <tr>
                    <td><span class="topten_header">Most Popular</span>
                        <ol>
                            <li py:for="project in popularProjects">
                                <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${project[1]}/">${project[2]}</a>
                            </li>
                        </ol>
                    </td>
                    <td><span class="topten_header">Most Active</span>
                        <ol>
                            <li py:for="project in activeProjects">
                                <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${project[1]}/">${project[2]}</a>
                            </li>
                        </ol>
                    </td>
                    <td><span class="topten_header">Recent Releases&nbsp;<a href="${basePath}rss?feed=newReleases"><img src="${cfg.staticPath}apps/mint/images/rss-inline.gif" alt="RSS" /></a></span>
                        <ol py:if="releases">

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
