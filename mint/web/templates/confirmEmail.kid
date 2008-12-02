<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Email Confirmation Required')}</title>
    </head>
    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
            <div class="full-content">
                <div class="page-title-no-project">Email Confirmation Required</div>
                
                <p class="errormessage">You have been redirected to this page because you have not yet confirmed your email address</p>
                <p>You will be required to do so before continuing.</p>
                <p>If you would like to use a different email address, please enter it below</p>
                <form method="post" action="editUserSettings">
                    <input type="text" name="email" value="${auth.email}"/>
                    <p><button class="img" type="submit"><img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" /></button></p>
                </form>
           </div>
            <br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>    

