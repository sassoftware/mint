<?xml version='1.0' encoding='UTF-8'?>
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
            <div id="right" class="side">
                ${projectsPane()}
            </div>
            <div id="middle">
                <h1 id="pleaseWait">Cooking Group: Choose An Architecture</h1>

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
                    <p>
                    </p>

                    <h3>Options</h3>
                    <dl class="archOptions">
                        <dt py:if="False">
                            <input name="flavor" type="checkbox" value="5#use:vmware" id="vmware" />
                            <label id="vmwareLabel" for="vmware">VMware tools support</label>
                        </dt>
                        <dd class="help" py:if="False">
                            Check this box to add VMware guest tools to this group.
                        </dd>
                        <dt>
                            <input name="flavor" type="checkbox" value="5#use:domU:xen" id="domU" />
                            <label id="domULabel" for="domU">Xen DomU (unprivileged guest) support</label>
                        </dt>
                        <dd class="help">
                            Check this box to add Xen guest domain (DomU)
                            support to this group. See the <a href="http://wiki.rpath.com/">rPath Wiki</a> for more
                            information about Xen and rBuilder.
                        </dd>
                        <dt py:if="False">
                            <input name="flavor" type="checkbox" value="5#use:kernel.pae" id="pae" />
                            <label id="paeLabel" for="pae">PAE (physical address extension) support
                            </label>
                        </dt>
                        <dd class="help" py:if="False">
                            Check this box to use a PAE-enabled kernel for this group. This is
                            required for Xen Enterprise guests and some other Xen Dom0 hypervisors.
                        </dd>
                    </dl>
                    <p><button class="img" type="submit"><img src="${cfg.staticPath}/apps/mint/images/cook_button.png" alt="Cook Group" /></button></p>
                    <input type="hidden" name="id" value="${groupTroveId}" />
                </form> 
            </div>
        </div>
    </body>
</html>
