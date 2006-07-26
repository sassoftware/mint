<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
from mint import buildtypes
from mint import userlevels
from mint.helperfuncs import truncateForDisplay
from mint.web.templatesupport import downloadTracker
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Project Build')}</title>
        <script type="text/javascript">
            <![CDATA[
                addLoadEvent(function() {roundElement('statusAreaHeader', {'corners': 'tl tr'})});
            ]]>
            <div py:if="isWriter" py:strip="True">
                <![CDATA[
                    addLoadEvent(function() {getBuildStatus(${build.id})});
                ]]>
            </div>
        </script>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(projectPublishedReleases, isOwner)}
                ${commitsMenu(projectCommits)}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen=30)}</h1>
                <h2>Build: ${name}</h2>

                <div py:if="isWriter and not build.getPublished()" py:strip="True">
                    ${statusArea("Build")}
                    <div id="editOptions" py:attrs="{ 'style': buildInProgress and 'display: none;' or None }">
                        <form id="editBuildOptions" action="editBuild" method="post">
                            <input type="hidden" name="buildId" value="${build.id}" />
                            <input type="submit" name="action" value="Edit Build" /> &nbsp;
                            <input type="submit" name="action" value="Recreate Build" />
                        </form>
                    </div>
                </div>

                <h3>Details</h3>

                <table class="troveinfo">
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
                        <th>Type</th>
                        <td>${buildtypes.typeNames[build.getBuildType()]}</td>
                    </tr>
                    <tr>
                        <th>Built By</th>
                        <td><span py:if="builtBy" py:strip="True"><a href="http://${SITE}userInfo?id=${builtBy.id}">${builtBy.username}</a></span><span py:if="not builtBy" py:strip="True">Unknown</span></td>
                    </tr>
                    <tr py:if="not buildInProgress and builtAt">
                        <th>Built At</th>
                        <td>${builtAt}</td>
                    </tr>
                </table>

                <h3>Notes</h3>
                <?python notes = build.getDesc().strip()?>
                <div py:if="notes" py:content="notes" />
                <div py:if="not notes">This build has no notes.</div>

                <div py:strip="True" py:if="not buildInProgress">
                    <h3>Downloads</h3>

                    <div py:if="files" py:strip="True">
                        <ul>
                            <li py:for="i, file in enumerate(files)">
                                <?py fileUrl = cfg.basePath + "downloadImage/" + str(file['fileId']) + "/" + file['filename'] ?>
                                <a py:attrs="downloadTracker(cfg, fileUrl)" href="http://${cfg.siteHost}${fileUrl}">${file['title'] and file['title'] or "Disc " + str(i+1)}</a> (${file['size']/1048576}&nbsp;MB)</li>
                        </ul>
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
                    </div>
                    <p py:if="not files">Build contains no downloadable files.</p>
                </div>
            </div>
        </div>
    </body>
</html>
