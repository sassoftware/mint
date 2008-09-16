<?xml version='1.0' encoding='UTF-8'?>
<?python from mint import constants ?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Group Builder: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            
            <div id="innerpage">
                <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                
                <div id="right" class="side">
                    ${projectsPane()}
                </div>
            
                <div id="middle">
                    <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                    <div id="pleaseWait" class="page-title">
                    Cooking a Group</div>
                    
                    <h2>Choose An Architecture</h2>
                    <p>Choose an architecture for which to cook this group. If you
                    want your application image to support multiple architectures, cook the group
                    for each architecture you wish to support.</p>

                    <form method="post" action="cookGroup">
                        <p>
                        <select name="flavor" id="buildArch">
                            <option value="1#x86">x86 (32-bit)</option>
                            <option value="1#x86_64">x86_64 (64-bit)</option>
                        </select>

                        </p>


                    <h2>Options</h2>
                    <table class="archOptions">
                    <tr py:if="False">
                        <td>
                            <input name="flavor" type="checkbox" value="5#use:vmware" id="vmware" />
                        </td>
                        <td class="label">
                            <label id="vmwareLabel" for="vmware">VMware tools support</label>
                            <p class="help">Check this box to add VMware guest tools to this group.</p>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input name="flavor" type="checkbox" value="5#use:domU:xen" id="domU" />
                        </td>
                        <td class="label">
                            <label id="domULabel" for="domU">DomU (unprivileged guest) support</label>
                            <div class="help">Check this box to add paravirtualization (DomU)
                            support to this group. See the <a href="http://wiki.rpath.com/?version=${constants.mintVersion}">rPath Wiki</a>
                            for moreinformation about paravirtualization and rBuilder.</div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input name="flavor" type="checkbox" value="5#use:kernel.pae" id="pae" />
                        </td>
                        <td class="label">
                            <label id="paeLabel" for="pae">PAE (physical address extension) support</label>
                            <div class="help">Check this box to use a PAE-enabled kernel for this group. This may
                            be required for some 32-bit Dom0.</div>
                        </td>
                    </tr>
                    </table>
                    <p class="p-button"><button class="img" type="submit"><img src="${cfg.staticPath}/apps/mint/images/cook_button.png" alt="Cook Group" /></button></p>
                    <input type="hidden" name="id" value="${groupTroveId}" />
                </form> 
                </div><br class="clear" />
                <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
