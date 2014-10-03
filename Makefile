all:
	echo 'WIP'

launch_dev_api:
	docker run --rm=true -t -i --name 'c9hub-api' -v `pwd`:/usr/src/app --expose='3232' -v '/var/run/docker.sock:/var/run/docker.sock' -v '/var/tmp/sites-enabled' 'tai_ide/hub_common:v0' c9hub-api

launch_dev_dashboard:
	docker run --rm=true -t -i --name 'c9hub-dashboard' -v `pwd`:/usr/src/app --expose='8080' --link 'c9hub-api:c9hub-api' 'tai_ide/hub_common:v0' c9hub-dashboard

#docker run --name some-nginx -v "$(pwd)/etc/docker/c9hub-nginx/nginx:/etc/nginx" --link 'c9hub-dashboard:c9hub-dashboard' --rm=true -P -t -i 'nginx:1.7.5' /bin/bash
#-v '/etc/nginx/site-enabled' 
launch_nginx:
	docker run --rm=true -t -i --name frontend-nginx -v "`pwd`/etc/docker/c9hub-nginx/nginx:/etc/nginx" --volumes-from='c9hub-api' --link 'c9hub-dashboard:c9hub-dashboard' --expose='443' -p '0.0.0.0:443:443' 'nginx:1.7.5'
