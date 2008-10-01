<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Lost Password')}</title>
    </head>
    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
            <div class="full-content">
                <div class="page-title-no-project">Lost Password</div>
                <form method="post" action="resetPassword">
                    <p>
                        If you have forgotten your password, please enter
                        your username and a new password will be emailed to you.
                    </p>
                    <p>
                    Username: <input class="email-address" type="text" autocomplete="off" name="username" />
                    </p>
                    <p><button class="img" type="submit"><img src="${cfg.staticPath}/apps/mint/images/reset_password.png" alt="Reset Password" /></button></p>
                </form>
            </div>
            <br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>
