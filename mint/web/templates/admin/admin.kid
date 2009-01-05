<?xml version='1.0' encoding='UTF-8'?>
<?python
    from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">

<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->

    <div py:def="adminResourcesMenu" id="admin" class="palette">
        <?python
            lastchunk = req.uri[req.uri.rfind('/')+1:]
        ?>
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />
        <div class="boxHeader"><span class="bracket">[</span> Administration Menu <span class="bracket">]</span></div>
        <ul class="navigation">
            <li py:attrs="{'class': (lastchunk in ('', 'admin')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/">Administration Home</a></li>
            <li py:attrs="{'class': (lastchunk in ('newUser', 'processNewUser')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/newUser">Create User Account</a></li>
            <li py:attrs="{'class': (lastchunk in ('external', 'addExternal', 'processAddExternal')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/external">Externally-Managed ${projectText().title()}s</a></li>
            <li py:attrs="{'class': (lastchunk in ('updateServices', 'editUpdateService', 'processEditUpdateService')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/updateServices">Configure Update Services</a></li>
            <li py:attrs="{'class': (lastchunk in ('outbound', 'editOutbound', 'processEditOutbound')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/outbound">Configure Outbound Mirroring</a></li>
            <li py:attrs="{'class': (lastchunk == 'maintenance') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/maintenance">Manage Maintenance Mode</a></li>
            <li py:if="cfg.rBuilderOnline" py:attrs="{'class': (lastchunk == 'reports') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/reports">View Reports</a></li>
            <li py:if="cfg.rBuilderOnline" py:attrs="{'class': (lastchunk == 'selections') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/selections">Manage Front Page Selections</a></li>
<<<<<<< local
            <li py:if="not cfg.rBuilderOnline" py:attrs="{'class': (lastchunk == 'setup') and 'selectedItem' or None}"><a href="${cfg.basePath}setup/">Re-run Initial Setup</a></li>
            <li py:if="not cfg.rBuilderOnline" py:attrs="{'class': (lastchunk == 'rAA')}"><a href="https://${cfg.hostName}.${cfg.siteDomainName.split(':')[0]}:8003/" target="_blank">More Administrative Options</a></li>
=======
            <li py:if="not cfg.rBuilderOnline" py:attrs="{'class': (lastchunk == 'rAA')}"><a href="https://${cfg.hostName}.${cfg.siteDomainName.split(':')[0]}:8003/" target="_blank">Enter rPath Appliance Agent</a></li>
>>>>>>> other
        </ul>
    </div>

</html>
