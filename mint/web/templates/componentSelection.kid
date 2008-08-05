<?xml version='1.0' encoding='UTF-8'?>
<?python
import simplejson
from mint.helperfuncs import truncateForDisplay

if 'message' not in locals():
    message = None

?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Appliance Creator: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
    <?python
        values = [
            #Tomcat + mysql
            {
                'stackId': 0,
                'name': 'Tomcat + MySQL',
                'short-desc': "Java application server which utilizes the popular Open Source Database MySQL",
                'status': 'production',
                'component-list': ['tomcat-6.2', 'jre-1.6.2', 'mysql-5.1'],
            },
            #Tomcat + mysql
            {
                'stackId': 0,
                'name': 'Tomcat + MySQL',
                'short-desc': "Java application server which utilizes the popular Open Source Database MySQL",
                'component-list': ['tomcat-6.2', 'jre-1.6.2', 'mysql-5.1', 'foo-9.1'],
                'status': 'production',
            },
            #Tomcat + mysql
            {
                'stackId': 0,
                'name': 'Tomcat + MySQL',
                'short-desc': "Java application server which utilizes the popular Open Source Database MySQL",
                'component-list': ['tomcat-6.2', 'jre-1.6.2', 'mysql-5.1'],
                'status': 'production',
            },
            #Tomcat + mysql
            {
                'stackId': 0,
                'name': 'Tomcat + MySQL',
                'short-desc': "Java application server which utilizes the popular Open Source Database MySQL",
                'component-list': ['tomcat-6.2', 'jre-1.6.2', 'mysql-5.1'],
                'status': 'production',
            },
            #Tomcat + mysql
            {
                'stackId': 0,
                'name': 'Tomcat + MySQL',
                'short-desc': "Java application server which utilizes the popular Open Source Database MySQL",
                'component-list': ['tomcat-6.2', 'jre-1.6.2', 'mysql-5.1'],
                'status': 'production',
            },
            #Tomcat + mysql
            {
                'stackId': 0,
                'name': 'Tomcat + MySQL',
                'short-desc': "Java application server which utilizes the popular Open Source Database MySQL",
                'component-list': ['tomcat-6.2', 'jre-1.6.2', 'mysql-5.1'],
                'status': 'production',
            },
        ]
    ?>
        <div id="layout">
            <div id="left" class="side">
                Next steps go here
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <style>
.component {
width: 140px;
float: left;
margin: 0.5em;
}

.production {
background-color: #11ff00;
color: #ffffff;
}

div.production .component_radio
{
    background-color: #55ff55;
}

.component_desc {
    padding: 0.5em;
}
            </style>

            <div id="middle">
            <p py:if="message" class="message" py:content="message"/>
            <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
            <h2>Appliance Creator: Select Application Stacks</h2>
            <div>
            <form action="saveComponents" method="post" name="selectComponents">
                <div py:for="en, stack in enumerate(values)" py:strip="True">
                  <div class="component ${stack['status']}">
                    <div class="component_radio">
                      <input type="radio" name="app_stack" value="${stack['stackId']}" id="app_stack_radio_${stack['stackId']}"/>
                      <label for="app_stack_radio_${stack['stackId']}">${stack['name']}</label>
                    </div>
                    <div py:content="stack['short-desc']" class="component_desc"/>
                    <div class="component_list">
                      <ul>
                        <li py:for="item in stack['component-list']" py:content="item" />
                      </ul>
                    </div>
                  </div>
                  <div py:if="not((en+1) % 3)" style="clear: left">&nbsp;</div>
                </div>
            </form>
            </div>
            </div><!--middle-->
        </div>
    </body>
</html>
