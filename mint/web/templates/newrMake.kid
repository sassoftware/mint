<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('Create an rMake build')}</title>
    </head>
    <body>
        <div id="layout">
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="spanleft">
                <h1>New rMake build</h1>
                <form method="post" action="createrMake">
                    <input type="text" name="title" value="" size="16" maxlength="128"/>
                    <p class="help">Please choose a name for your rMake build. This name is simply for your convenience so you can track multiple rMake builds conveniently. This name is not used anywhere else.</p>
                    <p><button class="img" type="submit">
                        <img src="${cfg.staticPath}/apps/mint/images/create_button.png" alt="Create" />
                    </button></p>
                </form>
            </div>
        </div>
    </body>
</html>
