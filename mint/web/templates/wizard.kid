<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
<?python
# Copyright (c) 2008 rPath, Inc.
# All Rights Reserved

# This template needs to be included in py:extends so that the locals for
# the derived template are local here as well
?>

<div py:def="wizard_navigation()" id="appliance_creator" class="wizard-nav-palette">
    <?python
    from mint.helperfuncs import truncateForDisplay, formatProductVersion
    ?>
    <img class="left" src="${cfg.staticPath}apps/mint/images/wiz_header_blue_left.png" alt="" />
    <img class="right" src="${cfg.staticPath}apps/mint/images/wiz_header_blue_right.png" alt="" />
    <div class="boxHeader"><span class="bracket">[</span> Appliance Creator Wizard <span class="bracket">]</span></div>
        <ul class="wiz-navigation">
            <li py:for="step in sorted([x for x in wizard_steps.keys() if x not in wizard_maint_steps])" py:attrs="{'class': (wizard_position == step) and 'selectedItem' or (wizard_position > step) and 'completedItem' or None}">
                <span py:replace="wizard_steps[step][0]"/>
            </li>
            <li class="wiz-exit">
                <a href="${project.getUrl(baseUrl)}">Exit Appliance Creator</a>
            </li>
        </ul>
</div>
</html>
