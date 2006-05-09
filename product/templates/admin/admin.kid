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
            <li py:attrs="{'class': (lastchunk in ('newUser', 'processNewUser')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/newUser">Create User Account</a></li>
            <li py:attrs="{'class': (lastchunk in ('sendNotify', 'notify')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/notify">Notify All Users</a></li>
            <li py:attrs="{'class': (lastchunk == 'reports') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/reports">View Reports</a></li>
            <li py:attrs="{'class': (lastchunk == 'external') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/external">Add Externally-Managed Project</a></li>
            <li py:attrs="{'class': (lastchunk in ('outbound', 'addOutbound')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/outbound">Outbound Mirror Settings</a></li>
            <li py:attrs="{'class': (lastchunk == 'jobs') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/jobs">Manage Jobs</a></li>
            <li py:attrs="{'class': (lastchunk == 'maintenance') and 'selectedItem' or None}"><a href="${cfg.basePath}admin/maintenance">Manage Maintenance Mode</a></li>
            <li py:attrs="{'class': (lastchunk == 'rAA')}"><a href="https://${cfg.hostName}.${cfg.siteDomainName}/rAA/" target="_blank">Entitlements, Updates, and Other System Operations</a></li>
        </ul>
    </div>

</html>
