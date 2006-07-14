<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
from mint import jobstatus
from mint import buildtypes
from mint import userlevels
from mint.helperfuncs import truncateForDisplay
from mint.web.templatesupport import downloadTracker
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <?python
    isOwner = (userLevel == userlevels.OWNER or auth.admin)
    isWriter = (userLevel in userlevels.WRITERS or auth.admin)
    if isWriter:
        onload = "getBuildStatus(" + str(build.getId()) + ");"
    else:
        onload = None

    bodyAttrs = {'onload': onload}
    ?>
    <head>
        <title>${formatTitle('Project Build')}</title>
    </head>
    <body py:attrs="bodyAttrs">
        <?python
            if isWriter:
                job = build.getJob()
            else:
                job = None

            if job and job.getStatus() > jobstatus.RUNNING:
                editOptionsStyle = ""
                editOptionsDisabledStyle = "color: gray; font-style: italic; display: none;"
            else:
                editOptionsStyle = "display: none;"
                editOptionsDisabledStyle = "color: gray; font-style: italic;"

        ?>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                <!-- FIXME: releases, not builds
                ${buildsMenu(publishedBuilds, isOwner) -->
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen=30)}</h1>
                <h2>Build Information</h2>

                <table>
                    <tr colspan="2">
                        <th style="font-size: larger;">${name}</th>
                    </tr>
                    <tr py:if="isWriter and not build.getPublished()">
                        <td colspan="2" id="jobStatusDingus">
                            <img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" id="spinner" style="float: right;"/>
                            <div id="statusMessage" class="running" />
                        </td>
                    </tr>
                    <tr>
                        <th>Group</th>
                        <td>${build.getTroveName()}</td>
                    </tr>
                    <tr>
                        <th>Version</th>
                        <td>${str(version.trailingRevision())}</td>
                    </tr>
                    <tr>
                        <th>Flavor</th>
                        <td>${str(build.getTroveFlavor()).replace(',', ', ')}</td>
                    </tr>
                    <tr>
                        <th>Architecture</th>
                        <td>${build.getArch()}</td>
                    </tr>
                    <tr>
                        <th>Release Type</th>
                        <td>${buildtypes.typeNames[build.getBuildType()]}</td>
                    </tr>
                    <tr>
                        <th>Build Notes</th>
                        <td>${build.getDesc().strip() or "This build has no notes."}</td>
                    </tr>
                    <tr>
                        <th>Built By</th>
                        <td>TBD</td>
                    </tr>
                    <tr>
                        <th>Build Time</th>
                        <td>TBD</td>
                    </tr>
                    <tr>
                        <th>Downloads</th>
                        <td py:if="files">
                            <div py:strip="True" py:for="i, file in enumerate(files)">
                                <?py fileUrl = cfg.basePath + "downloadImage/" + str(file['fileId']) + "/" + file['filename'] ?>
                                <a py:attrs="downloadTracker(cfg, fileUrl)" href="http://${cfg.siteHost}${fileUrl}">
                                    ${file['title'] and file['title'] or "Disc " + str(i+1)}
                                </a> (${file['size']/1048576}&nbsp;MB)<br />
                            </div>
                        </td>
                        <td py:if="not files">
                            Build has no downloadable files.
                        </td>
                    </tr>
                    <tr py:if="files">
                        <td colspan="2">
                            <div py:strip="True" py:if="buildtypes.INSTALLABLE_ISO == build.buildType">
                                <h4 onclick="javascript:toggle_display('file_help');" style="cursor: pointer;">What are these files?&nbsp;<img id="file_help_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /></h4>

                                <div id="file_help" style="display: none;">
                                    <p>The file(s) entitled <tt>Disc <em>N</em></tt>
                                    represent the disc(s) required to install this
                                    build. These files are in ISO 9660 format, and can be
                                    burned onto CD or DVD media using the CD/DVD burning
                                    software of your choice. The installation process is
                                    then started by booting your system from a disc
                                    burned from the file entitled <tt>Disc 1</tt>.</p>

                                    <p>The last two files are used only if you want to
                                    perform a network installation.  To do so, you must
                                    first download all "Disc N" file(s) and export them
                                    (via NFS).  You can then download and use one of the
                                    following files to boot the system to be installed:</p>

                                    <ul>
                                        <li>Use the <tt>boot.iso</tt> file if your system
                                        can boot from CD/DVD. This file is an ISO 9660
                                        image of a bootable CD-ROM, and can be burned onto
                                        CD or DVD  media using the CD/DVD burning software
                                        of your choice.</li>

                                        <li>Use the <tt>diskboot.img</tt> file if your
                                        system cannot boot from CD/DVD, but can boot from
                                        some other type of bootable device. This file is a
                                        VFAT filesystem image that can be written (using
                                        the <tt>dd</tt> command) to a USB pendrive
                                        or other bootable media larger than a
                                        diskette.  Note that your system's BIOS
                                        must support booting from USB to use this
                                        file with any USB device.</li>
                                    </ul>
                                </div>
                            </div>

                            <div py:strip="True" py:if="buildtypes.VMWARE_IMAGE == build.buildType">
                                <h4 onclick="javascript:toggle_display('file_help');" style="cursor: pointer;">What is this file?&nbsp;<img id="file_help_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /></h4>

                                <div id="file_help" style="display: none;">
                                    <p>This file contains the <tt>.vmdk</tt> and
                                    <tt>.vmx</tt> files usable by VMware
                                    Player.</p>

                                    <p>NOTE: Before using this file, you must unzip
                                    it using the utility of your choice.  However,
                                    be aware that some unzip utilities cannot
                                    correctly uncompress a zipped file if one of
                                    the files in the zip archive is larger than
                                    2GB.  If this file contains a <tt>.vmdk</tt>
                                    file larger than 2GB (you can use the
                                    <tt>zipinfo</tt> command to find out), you may
                                    experience this.  Note that the <tt>unzip</tt>
                                    utility packaged with rPath Linux can
                                    unzip files larger than 2GB.</p>
                                </div>
                            </div>

                            <div py:strip="True" py:if="buildtypes.RAW_HD_IMAGE == build.buildType">
                                <h4 onclick="javascript:toggle_display('file_help');" style="cursor: pointer;">What is this file?&nbsp;<img id="file_help_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /></h4>

                                <div id="file_help" style="display: none;">
                                    <p>This file contains an image of a bootable
                                    environment capable of being written onto an
                                    IDE disk drive using the <tt>dd</tt> command.
                                    This image can also be run under the <a
                                    href="http://fabrice.bellard.free.fr/qemu/">QEMU</a>
                                    processor emulator.</p>

                                    <p>NOTE: This image has been compressed using
                                    GNU zip.  Before using this image, you must
                                    first uncompress it (using the <tt>gunzip</tt>
                                    command).</p>
                                </div>
                            </div>

                            <div py:strip="True" py:if="buildtypes.RAW_FS_IMAGE == build.buildType">
                                <h4 onclick="javascript:toggle_display('file_help');" style="cursor: pointer;">What is this file?&nbsp;<img id="file_help_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /></h4>

                                <div id="file_help" style="display: none;">
                                    <p>This file contains a system environment
                                    in a single filesystem (it includes no
                                    partition table).  It can be written onto
                                    an IDE disk drive using the <tt>dd</tt>
                                    command.</p>

                                    <p>NOTE: This image has been compressed using
                                    GNU zip.  Before using this image, you must
                                    first uncompress it (using the <tt>gunzip</tt>
                                    command).</p>
                                </div>
                            </div>

                            <div py:strip="True" py:if="buildtypes.TARBALL == build.buildType">
                                <h4 onclick="javascript:toggle_display('file_help');" style="cursor: pointer;">What is this file?&nbsp;<img id="file_help_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /></h4>

                                <div id="file_help" style="display: none;">
                                    <p>This file contains a system environment
                                    in tar format, compressed using GNU zip.
                                    Before using this image, you must first
                                    uncompress it (using the <tt>gunzip</tt>
                                    command).</p>
                                </div>
                            </div>

                            <div py:strip="True" py:if="buildtypes.LIVE_ISO == build.buildType">
                                <h4 onclick="javascript:toggle_display('file_help');" style="cursor: pointer;">What is this file?&nbsp;<img id="file_help_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /></h4>

                                <div id="file_help" style="display: none;">
                                    <p>This file contains a system environment
                                    capable of being booted and run directly
                                    from a CD/DVD.  The file is in ISO 9660
                                    format, and can be burned onto CD or DVD
                                    media using the CD/DVD burning software of
                                    your choice.</p>
                                </div>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    </body>
</html>
