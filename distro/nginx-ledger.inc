location = / { rewrite .* /SASvAppLedger redirect; }
location /SASvAppLedger { proxy_pass http://127.0.0.1:18081; }
location /files { alias /opt/sasinside/var/content/www/html/files; }
