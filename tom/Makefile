clean:
	rm -f *.pyc error_log access_log httpd.pid

run:
	#sh -c 'ipcs  -s  | awk "/^0x/ {print $2}" | xargs -n1 -r ipcrm -s'
	PYTHONPATH=. httpd -X -d . -C "DocumentRoot ." -f ./httpd.conf

stop:
	kill $(cat httpd.pid)
