<?xml version='1.0' encoding='UTF-8'?>
<?python
from conary.lib.cfg import *
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('rBuilder Configuration')}</title>
    </head>
    <body>
        <div class="layout">
            <h1>rBuilder Configuration</h1>

            <p>Before we configure your rBuilder server, we must first
            ensure that only the person that initiated the installation
            process has access to the rBuilder configuration page.</p>

            <p>To enable access to the rBuilder configuration page, perform
            the following steps:</p>

            <ol>
                <li>Using the password you entered during the installation
                process, login to your rBuilder server by issuing the
                following command:<br/><br/>

                <strong><tt>ssh ${req.hostname}</tt></strong><br/><br/></li>

                <li>Once logged in, issue the following command:<br/><br/>
                <strong><tt>touch ${cfg.dataPath}${sid}.txt</tt></strong><br/><br/></li>

                <li>Reload this page by pressing your browser's reload
                button</li>
            </ol>

            <p>At this point, you and only you will have access to the
            rBuilder configuration page.</p>
        </div>
    </body>
</html>
