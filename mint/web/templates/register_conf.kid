<?xml version='1.0' encoding='UTF-8'?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Thank You for Registering')}</title>
    </head>

    <div py:def="stepContent">
        Check your email and follow the link enclosed.
    </div>

    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
            <div id="left" class="side">
                 ${stepsWidget(['Get Started', 'Sign Up', 'Confirm Email'], 2)}
            </div>
            
            <div id="centerright">
                <div class="page-title-no-project">Thank you for registering</div>
                <p>An email confirming your request has been sent to the email address you provided.</p>
                <p>Please follow the directions in your confirmation email to complete the registration process.</p>
                
            </div><br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>