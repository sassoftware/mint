<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">

    <div py:def="adminResourcesMenu" id="admin" class="palette">
        <?python
            lastchunk = req.uri[req.uri.rfind('/')+1:]
        ?>
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />
        <div class="boxHeader">Administration Menu</div>
        <ul>
            <li py:attrs="{'class': (lastchunk in ('', 'admin')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/">Administration Home</a></li>
            <li py:attrs="{'class': (lastchunk == 'jobs') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/jobs">Manage Jobs</a></li>
            <li py:attrs="{'class': (lastchunk == 'reports') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/reports">View Reports</a></li>
            <li py:attrs="{'class': (lastchunk in ('newUser', 'processNewUser')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/newUser">Create User Account</a></li>
            <li py:attrs="{'class': (lastchunk in ('external', 'addExternal', 'processAddExternal')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/external">Externally-Managed Projects</a></li>
            <li py:attrs="{'class': (lastchunk in ('outbound', 'addOutbound')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/outbound">Configure Outbound Mirroring</a></li>
            <li py:attrs="{'class': (lastchunk == 'maintenance') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/maintenance">Manage Maintenance Mode</a></li>
            <li py:attrs="{'class': (lastchunk == 'spotlight') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/spotlight">Manage Appliance Spotlight</a></li>
            <li py:attrs="{'class': (lastchunk == 'selections') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/selections">Manage Front Page Selections</a></li>
            <li py:attrs="{'class': (lastchunk == 'useIt') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/useIt">Manage 'Use It' Icons</a></li>
            <li py:attrs="{'class': (lastchunk == 'setup') and 'selectedItem' or None}"><a href="${cfg.basePath}setup/">Re-run Initial Setup</a></li>
        </ul>
    </div>

</html>
