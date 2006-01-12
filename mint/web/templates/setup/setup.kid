<?xml version='1.0' encoding='UTF-8'?>
<?python
from conary.lib.cfg import *
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('rBuilder Product Setup')}</title>
    </head>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h1>rBuilder Product Setup</h1>
                <form action="processSetup" method="post">
                    <div py:for="group, groupItems in configGroups.items()">
                        <h2>${group}</h2>
                        <table class="mainformhorizontal" style="width: 100%;">
                            <tr py:for="i, key in enumerate(groupItems)">
                                <td style="width: 50%;">
                                    ${XML(cfg._options[key].__doc__ and cfg._options[key].__doc__ or key)}
                                </td>
                                <td py:if="isinstance(cfg._options[key].valueType, CfgBool)">
                                  <input class="check" type="checkbox" name="${key}" value="${cfg.__dict__[key]}"/>
                                </td>
                                
                                <td py:if="isinstance(cfg._options[key].valueType, CfgString)">
                                  <input style="width: 100%;" type="text" name="${key}" value="${cfg.__dict__[key]}"/>
                                </td>
                            </tr>
                        </table>
                    </div>
                <p><button type="submit">Save Changes</button></p>
              </form>
            </div>
        </td>
        <td id="right" class="projects">
            <div class="pad">
            </div>
        </td>
    </body>
</html>
