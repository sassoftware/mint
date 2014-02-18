#location /ui/imageUpload            { alias /usr/share/rbuilder-ui/plupload/plupload.html; }
#location /ui/plupload               { alias /usr/share/rbuilder-ui/plupload/plupload; }
#location /ui/modules                { alias /usr/share/rbuilder-ui/modules; }
#location /ui/hooks                  { alias /usr/share/rbuilder-ui/modules/hooks; }
#location /ui/themes                 { alias /usr/share/rbuilder-ui/themes; }
#location /ui                        { alias /usr/share/rbuilder-ui; }
location /schemas                   { alias /usr/share/rbuilder-ui/xml_resources/xsd; }
location /crossdomain.xml           { alias /usr/share/rbuilder-ui/crossdomain.xml; }
