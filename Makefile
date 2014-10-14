all:
	echo 'WIP'

launch_dev_api:
	docker run --rm=true -t -i --name 'c9hub-api' -v `pwd`:/usr/src/app --expose='3232' -v '/var/run/docker.sock:/var/run/docker.sock' 'tai_ide/hub_common:v0' c9hub-api

launch_dev_dashboard:
	docker run --rm=true -t -i --name 'c9hub-dashboard' -e 'C9HUB_API_CONF_FILEPATH=y.yaml' -v `pwd`:/usr/src/app --expose='8080' --link 'c9hub-api:c9hub-api' 'tai_ide/hub_common:v0' c9hub-dashboard

#docker run --name some-nginx -v "$(pwd)/etc/docker/c9hub-nginx/nginx:/etc/nginx" --link 'c9hub-dashboard:c9hub-dashboard' --rm=true -P -t -i 'nginx:1.7.5' /bin/bash
#-v '/etc/nginx/site-enabled' 

#docker run --rm=true -t -i --name frontend-nginx -v "`pwd`/etc/docker/c9hub-nginx/nginx:/etc/nginx" --volumes-from='c9hub-api' --link 'c9hub-dashboard:c9hub-dashboard' --expose='443' -p '0.0.0.0:443:443' 'tai_ide/nginx:v0' find /var/opt/cloud9 -iname '*default.js'
#docker run --rm=true -t -i --name frontend-nginx -v "`pwd`/etc/docker/c9hub-nginx/nginx:/etc/nginx" --volumes-from='c9hub-api' --link 'c9hub-dashboard:c9hub-dashboard' --expose='443' --expose 8080 -p '0.0.0.0:443:443' -p '0.0.0.0:8080:8080' 'nginx:1.7.5'
launch_nginx:
	docker run --rm=true -t -i --name frontend-nginx -v '/var/run/docker.sock:/var/run/docker.sock' -v "`pwd`/etc/docker/c9hub-nginx/nginx:/etc/nginx" -v "`pwd`/etc/docker/c9hub-nginx/app:/app" --link 'c9hub-dashboard:c9hub-dashboard' --expose='443' --expose '8080' -p '0.0.0.0:443:443' -p '0.0.0.0:8080:8080' 'tai_ide/nginx:v0'

build_hub_common:
	docker build --rm=true -t 'tai_ide/hub_common:v0' .


#docker tag tai_ide/hub_common:v0 130.206.85.162:5000/tai_ide/hub_common:v0

launch_static:
	docker run -d --name 'backend-static-c9' 'tai_c9/cloud9:v0' ./start_c9.sh