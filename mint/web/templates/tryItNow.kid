<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2007 rPath, Inc.
# All Rights Reserved
#
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle("Try It Now!")}</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/ec2.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript">
            <![CDATA[
                addLoadEvent(function() { launcher = new EC2Launcher(${blessedAMIId}); });
            ]]>
        </script>
    </head>
    <body>
        <div id="layout">
            <div id="right" class="side">
                ${resourcePane()}
            </div>

                <h1>Try It Now</h1>
                <h2>${shortDescription}</h2>


                <div id="div_before_launch">
                    <p><img style="float: left; margin-right: 0.5em; margin-bottom: 5em;" src="${cfg.staticPath}apps/mint/images/amazon.gif" alt="Amazon Web Services" />This appliance can be run in the Amazon Elastic Compute Cloud (EC2), compliments of rPath. Click on the button below to launch the appliance. Once the boot process is complete, additional instructions will appear and you can complete the installation. Then, use the ${shortDescription} appliance in the cloud!</p>
                    <p><button id="startButton">Launch It!</button></p>
                </div>

                <div id="div_during_launch" style="display: none;">
                    <p><img style="margin-right: 0.25em;" src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" />&nbsp;Your image is being established in the cloud. Do not browse away from this page until the process is complete.</p>
                </div>

                <div id="div_success" style="display: none;">
                    <h3>Success!</h3>
                    <p>Your instance has been launched on Amazon's EC2 service and is ready to try out. You may now visit the appliance's web-based administration page by <a id="rapLink" href="#" target="new">clicking here</a>. The login information for your appliance is as follows:</p>
                    <table style="width: auto; font-family: monospace;">
                        <tbody>
                            <tr>
                                <td>Username:</td>
                                <td>admin</td>
                            </tr>
                            <tr>
                                <td>Password:</td>
                                <td id="rapPassword">password</td>
                            </tr>
                        </tbody>
                    </table>
                    <div py:if="helptext"><h3>Additional Information</h3><p>${helptext}</p></div>
                </div>

                <div id="div_failure" style="display: none;">
                    <h3>Uh-oh...</h3>
                    <p>There was a problem launching your instance within the cloud. Please try again later.</p>
                </div>
        </div>
    </body>
</html>
