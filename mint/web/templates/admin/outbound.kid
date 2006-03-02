<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'administer.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        ${adminbreadcrumb()}
        <a href="administer?operation=external">Outbound Mirroring</a>
    </div>

    <head>
        <title>${formatTitle('Outbound Mirroring')}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
                <form action="administer" method="post">
                    <h2>Outbound Mirroring</h2>
                    <p class="help">
                        You can select projects in ${cfg.productName} to be mirrored out to
                        an external Conary repository.
                    </p>

                    <h3>Projects Currently Mirrored</h3>
                    <table py:if="outboundLabels" class="outboundMirrors">
                        <tr style="font-weight: bold; background: #eeeeee;">
                            <td>Project</td>
                            <td>Label Mirrored</td>
                            <td>Target Repository</td>
                            <td>Remove</td>
                        </tr>
                        <tr py:for="project, label, labelId, url, user, passwd in outboundLabels">
                            <td><a href="${project.getUrl()}">${project.name}</a></td>
                            <td>${label[0]}</td>
                            <td>${url}</td>
                            <td><input type="checkbox" name="remove" value="${labelId} $url" /></td>
                        </tr>
                    </table>
                    <div py:if="not outboundLabels">
                        No projects are currently mirrored.
                    </div>
                    <button py:if="outboundLabels" style="float: right;" type="submit" name="operation" value="remove_outbound">Remove Selected</button>
                </form>
                <p style="clear: right;"><b><a href="administer?operation=add_outbound">Add an Outbound Mirror</a></b></p>
                <p><b><a href ="../administer/">Return to Administrator Page</a></b></p>
            </div>
        </td>
    </body>
</html>
