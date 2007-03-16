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
                ${builderPane()}
            </div>

                <h1>Try It Now</h1>
                <h2>${shortDescription}</h2>

                <div id="div_before_launch">
                    <p>This appliance is available as an <acronym title="Amazon Machine Image">AMI</acronym> in the Amazon Elastic Compute Cloud (Amazon EC2).  When you click on the button below, a new, private instance of this AMI will initiated. Instructions on how to use the image will appear when the image has finished booting.</p>
                    <p py:if="buildId">This <acronym title="Amazon Machine Image">AMI</acronym> was built using ${cfg.productName} (<a href="${basePath}build?id=${buildId}">more info</a>).</p>
                    <p><button id="startButton">Launch It!</button></p>
                </div>

                <div id="div_during_launch" style="display: none;">
                    <h3>Launching Your Appliance for Test Drive</h3>
                    <p><img style="margin-right: 0.25em;" src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" />${cfg.productName} is now launching your appliance. Do not browse away from this page!</p>
                </div>

                <div id="div_success" style="display: none;">
                    <h3>Success!</h3>
                    <p>Your instance has been launched on Amazon's EC2 service and is ready to try out. You may now visit the appliance's web-based administration page by <a id="rapLink" href="#" target="new">clicking here</a>.</p>
                    <table>
                        <tbody>
                            <tr>
                                <th colspan="2">Login Information</th>
                            </tr>
                            <tr>
                                <td>Username</td>
                                <td>admin</td>
                            </tr>
                            <tr>
                                <td>Password</td>
                                <td id="rapPassword">password</td>
                            </tr>
                        </tbody>
                    </table>
                    <div py:if="helptext"><h3>Additional Information</h3><p>${helptext}</p></div>
                </div>

                <div id="div_failure" style="display: none;">
                    <h3>Uh-oh...</h3>
                    <p>There was a problem launching your instance. Please try again later.</p>
                </div>



        </div>
    </body>
</html>
