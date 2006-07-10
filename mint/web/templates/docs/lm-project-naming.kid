<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'minihelp.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${cfg.productName} Help</title>
    </head>

    <body>
        <h2>Choosing a Project Domain Name</h2>
        <p>You do not need to make any changes from the default if the following points are <strong>both</strong> true:</p>

        <ul>
            <li>The software stored in this project's repository is destined to be used exclusively within your organization</li>
            <li>All the systems within your organization that will have this software installed will be able to access this project's repository using the fully-qualified domain name [projectname-and-defaultdomainname]</li>
        </ul>

        <p>However, if either of these points is not true, you must change the domain name field.  The exact domain name you enter depends on the specific details of your organization's situation; however, here are some common examples:</p>

        <ul>
            <li>An rBuilder project's repository is accessible via "project.devel.example.com", but the internal systems that will be installing software from the repository are part of the "buildion.example.com" network, and cannot resolve or access "project.devel.example.com".  In this case, enter "buildion.example.com" and refer to the note at the end of this page.</li>
            <li>An rBuilder project's repository is accessible via "project.devel.example.com, but the systems that will be installing software from this repository are external to the example.com network, and cannot resolve or access "project.devel.example.com".  In this case, enter "example.com" and refer to the note at the end of this page.</li>
        </ul>

        <p><strong>Note:</strong> The following issues must be addressed in some fashion when changing the default domain name:</p>

        <ul>
            <li><p>Development systems must have their <tt>/etc/conaryrc</tt> files modified so that Conary will be able to access this project's repository.  This can be done by either adding a <tt>repositoryMap</tt> entry mapping the repository's label to the fully-qualified domain name by which the repository can be accessed, or adding the following line to <tt>/etc/conaryrc</tt>, and relying on rBuilder's centralized <tt>repositoryMap</tt> registry:</p>

                <p><tt>includeConfigFile http://${cfg.hostName}.${cfg.siteDomainName}/conaryrc</tt></p>
            </li>

            <li>If the systems that will be installing software from this project do not have connectivity to the project's repository, a repository must be installed and configured in such a way that it can be mirrored from this project's repository, and is accessible to the systems that will be installing this software.  An rBuilder Mirror can be used for this purpose.</li>

        </ul>
    </body>
</html>
