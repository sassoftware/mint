<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Preload Mirror')}</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/mirror.js" />
    </head>
    <body>
        <div>
            <p>Please follow the instructions below to pre-load your mirror.</p>

            <div class="running" id="statusMessage">Insert the first mirror pre-loading disk and press the button below.</div>

            <p>
                <button onclick="getDiscInfo('${serverName}');" id="goButton">Start Import</button>
                <a style="display: hidden;" id="finishLink" href="/">Finish</a>
            </p>

        </div>
    </body>
</html>
