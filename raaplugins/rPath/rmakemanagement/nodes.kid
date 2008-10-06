<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<?python
import raa.templates.master
import raa.templates.tabbedpagewidget
from raa.web import makeUrl, getConfigValue
from rPath.rmakemanagement import pageList
?>

<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
      py:extends="raa.templates.master, raa.templates.tabbedpagewidget">

<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->   

<head>
    <title>${getConfigValue('product.productName')}: rMake Management</title>
</head>

<body>
    <?python
    instructions = "Manage rMake nodes"
    ?>

    <div class="plugin-page" id="plugin-page">
        <div class="page-content">
            <div py:if="raa.identity.ADMINROLE in raa.identity.current.permissions" py:strip="True">
                 ${TabbedPageWidget(forcepage='nodes', value=pageList)} 
            </div>
            <div py:replace="display_instructions(instructions, raaInWizard)"> </div>
        </div>
    </div>
</body>
</html>
