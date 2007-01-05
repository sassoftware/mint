<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('Preload Mirror')}</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/mirror.js?v={cacheFakeoutVersion}" />
    </head>
    <body>
        <div>
            <p>
                Please follow the instructions below to pre-load your mirror.
            </p>
            <h3 style="background: #FFDFD4; border-width: 1px; border-style: solid; border-color: #ff8077; padding: 5px;">
                Do not close this window or navigate away from this page while the operation is in progress.
            </h3>

            <div class="running" id="statusMessage">Insert the first mirror pre-loading disk and press the button below.</div>

            <p>
                <button onclick="getDiscInfo('${serverName}');" id="goButton">Start Import</button>
            </p>

            <p id="finishForm">
                <?python
                    kwargs = {'name': name, 'hostname': hostname, 'label': label,
                        'url': url, 'externalAuth': int(externalAuth),
                        'authType': authType, 'externalUser': externalUser,
                        'externalPass': externalPass,
                        'externalEntKey': externalEntKey,
                        'externalEntClass': externalEntClass,
                        'useMirror': int(useMirror), 'primeMirror': int(primeMirror)}
                ?>
                <form method="post" action="processExternal">
                    <button type="submit" style="display: none;" id="finishLink">Finish</button>
                    <input type="hidden" py:for="key, val in kwargs.items()" name="${key}" value="${val}" />
                </form>
            </p>

        </div>
    </body>
</html>
