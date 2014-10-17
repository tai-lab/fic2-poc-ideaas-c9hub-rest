# Development #

In the following explanations, the ip `192.168.103.116` refers to the host where the containers will be run.


## Step 1: Installing a local OAuth provider ##

The project is bound to an OAuth provider.
A local provider can be setup with `doorkeeper` to easily trace the flow of authentication.

First clone the `doorkeeper` project from github:

	tai@i-45-56875-VM:~/git$ git clone https://github.com/doorkeeper-gem/doorkeeper-provider-app.git

A patch the add ssl support must be applied with:

	tai@i-45-56875-VM:~/git/doorkeeper-provider-app$ git am ../tai-c9hub-rest/etc/oauth_doorkeeper/

Then all the code dependencies should be retrieve with:

	tai@i-45-56875-VM:~/git/doorkeeper-provider-app$ bundle install

The `doorkeeper` server is started with the command:

	tai@i-45-56875-VM:~/git/doorkeeper-provider-app$ thin --debug --trace start --ssl -p 3000

Or simply:

	tai@i-45-56875-VM:~/git/doorkeeper-provider-app$ make run


## Step 2: check oauth credentials ##

The default oauth credentials for the dashboard application are stored in the file: `c9hubdashboard/resources/etc/c9hubdashboard.default.yaml`.


## Step 3: create the images ##

**Important: the source code injected in the docker image is taken from the current git master head's reference. Unstaged and uncommitted changes are ignored.**

### Step 3.a: the `tai_c9/cloud9` image ###

This image contains the Cloud9 ide.
When a user orders an ide, a container running this image will be launched.

To create the image, launch the command inside the directory`cloud9/dockerfile`:

	tai@i-45-56875-VM:~/git/cloud9/dockerfile$ make

A `tai_c9/cloud9` image should now be present inside Docker.

	tai@i-45-56875-VM:~/git/cloud9/dockerfile$ docker images
	REPOSITORY                               TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
	tai_c9/cloud9                            v0                  6b4bb7ceab6a        24 hours ago        726.4 MB


### Step 3.b: the `tai_ide/hub_common` image ###

This image is the common image used to launch the dashboard and the api.

Inside the `tai-c9hub-rest` directory, use this command to build the image:

	make build_hub_common

Internally, this command is just an alias for:

	docker build --rm=true -t 'tai_ide/hub_common:v0' .


### Step 3.c: the `tai_ide/nginx` image ###

This image contains the nginx server, the frontend of the demo.
Nginx is used to support SSL offloading and to handle the routing between each ides.

Inside the `tai-c9hub-rest/etc/docker/c9hub-nginx` directory, launch the command:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest/etc/docker/c9hub-nginx$ make

### Step 3.d: checking the result ###

After all this steps, Docker should contains this 3 images:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest/etc/docker/c9hub-nginx$ docker images 
	REPOSITORY                               TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
	tai_c9/cloud9                            v0                  86b0dd6dc0f4        About an hour ago   726.4 MB
	tai_ide/nginx                            v0                  293cdde0787d        25 hours ago        121 MB
	tai_ide/hub_common                       v0                  c3e999592953        25 hours ago        1.021 GB

## Step 4: launch sequence & live coding ##

[launch_sequence]: #step-4-launch-sequence-live-coding

> **Important: the start order of the containers are important because it uses the `link` feature of Docker**

> **The dependencies are:**
>
	c9hub-api <--- c9hub-dashboard <--- frontend-nginx
	         backend-static-c9 <------/

> **If a container is stopped then all the containers up to the root container `frontend-nginx MUST be restarted.`**

During development, the images don't need to be rebuild after each modification.
A specific launch sequence is present for this purpose.
This possibility is made using the `volume` feature of docker and the reloading capabilities of python.
In this context, the following commands will launch each part of the demo:

For each of the 4 parts, a container will be launched interactively to see the output.

* For the api, any change inside the host's `tai-c9hub-rest` directory will be automatically reloaded with:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ make launch_dev_api

* For the dashboard, any change inside the host's `tai-c9hub-rest` directory will be automatically reloaded with:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ make launch_dev_dashboard

* For the neutral cloud 9 container:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ make launch_static	

* For the nginx frontend, any changes in the `~tai-c9hub-rest/etc/docker/c9hub-nginx/nginx` and the `tai-c9hub-rest/etc/docker/c9hub-nginx/app` directories will be applied when nginx is reloaded:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ make launch_nginx



# Production deployment #

For the deployment platform, all the servers are running the latest CoreOs image.
The deployment process required 2 hosts: `docker-registry` and `cloud-ides`.
The `cloud-ides` is the server hosting the api, the dashboard and the ides.
The `docker-registry` is the server hosting the Docker registry for managing images.


## Security group ##

Ports to open:

* `docker-registry`: 22, 5000
* `cloud-ides`: 22, 443, 8080


## About the Docker registry ##

An intermediate Docker registry must be put in place for the deployment.
After being setup, the registry can be reused without problem.
After developing, the built images will be pushed in the registry, then pulled inside the final deployment server.
Generally, the server providing the registry should be different than the server which will host the ides.


## Step 1: initial setup ##


### Step 1.a: Launching the Docker registry ###

On the `docker-registry` host, run the command:

	docker run -p 5000:5000 registry

This command will launch a private docker registry on the port 5000.

**With this simple setup, if the container is stopped, all the pushed images will be lost.**

TODO: systemd service


### Step 1.b: Configuring the `cloud-ides` host ###

On the `cloud-ides` server, a cron job must be created to clean the stopped ides containers.
First upload the `tai-c9hub-rest/etc/cron.conf` file on the host:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ scp etc/clean_ides_container.timer etc/clean_ides_container.service core@130.206.85.162:/tmp/
	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ ssh core@130.206.85.162 'sudo mv /tmp/clean_ides_container.* /etc/systemd/user/'

Then enable the timer to start at boot:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ ssh core@130.206.85.162 'systemctl enable /etc/systemd/user/clean_ides_container.timer'

Finally bootstrap the timer:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ ssh core@130.206.85.162 'systemctl start clean_ides_container.timer'


### Step 1.c: registering the OAuth provider ###

Copy the yaml configuration concerning the FiLab OAuth service inside the `cloud-ides` host.

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ scp etc/filab_oauth.yaml core@130.206.85.162:


## Step 2 [repeat]: dealing with images ##

**Requirements: all the images should be built and ready on your development host.**

For example:

    tai@i-45-56875-VM:~/git/tai-c9hub-rest$ docker images 
    REPOSITORY                               TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
    tai_ide/nginx                            v0                  293cdde0787d        About an hour ago   121 MB
    tai_ide/hub_common                       v0                  c3e999592953        About an hour ago   1.021 GB
    tai_c9/cloud9                            v0                  6b4bb7ceab6a        2 hours ago         726.4 MB
    python                                   3.4-onbuild         cf739b98f94b        8 days ago          968.3 MB
    python                                   3.4                 fbd8bb031d4b        8 days ago          968.3 MB
    ubuntu                                   14.04               6b4e8a7373fe        13 days ago         194.8 MB
    nginx                                    1.7.5               d2d79aebd368        2 weeks ago         100.2 MB


### Step 2.a: Tagging images ###

In all the following commands, the ip 130.206.85.162 refers to the docker-registry server.
If the images were already tagged and bound to an older version, they can be removed beforehand with:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ docker rmi 130.206.85.162:5000/tai_c9/cloud9

The tag are created with the commands:

	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ docker tag tai_ide/nginx:v0 130.206.85.162:5000/tai_ide/nginx:vO
	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ docker tag tai_ide/hub_common:vO 130.206.85.162:5000/tai_ide/hub_common:vO
	tai@i-45-56875-VM:~/git/tai-c9hub-rest$ docker tag tai_c9/cloud9:vO 130.206.85.162:5000/tai_c9/cloud9:vO

The result can be checked with the command:

    tai@i-45-56875-VM:~/git/tai-c9hub-rest$ docker images 
    REPOSITORY                               TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
    tai_ide/nginx                            v0                  293cdde0787d        About an hour ago   121 MB
    130.206.85.162:5000/tai_ide/nginx        v0                  293cdde0787d        About an hour ago   121 MB
    tai_ide/hub_common                       v0                  c3e999592953        About an hour ago   1.021 GB
    130.206.85.162:5000/tai_ide/hub_common   v0                  c3e999592953        About an hour ago   1.021 GB
    tai_c9/cloud9                            v0                  6b4bb7ceab6a        2 hours ago         726.4 MB
    130.206.85.162:5000/tai_c9/cloud9        v0                  6b4bb7ceab6a        2 hours ago         726.4 MB


### Step 2.a: Pushing the images ###

When the images are properly tagged and bound to the correct version, then they can be pushed to the docker-registry with:

	core@cloud-ides ~ $ docker push 130.206.85.162:5000/tai_ide/nginx:v0
	core@cloud-ides ~ $ docker push 130.206.85.162:5000/tai_ide/hub_common:v0
	core@cloud-ides ~ $ docker push 130.206.85.162:5000/tai_c9/cloud9:v0


## Step 3: Starting the application ##

**Important: [check the launch sequence][launch_sequence]**


	core@cloud-ides ~ $ pwd
	/home/core
	core@cloud-ides ~ $ docker run -d --name 'c9hub-api' --expose='3232' -v '/var/run/docker.sock:/var/run/docker.sock' '10.0.5.241:5000/tai_ide/hub_common:v0' c9hub-api
	core@cloud-ides ~ $ docker run -d --name 'c9hub-dashboard' -e 'C9HUB_API_CONF_FILEPATH=/tmp/filab_oauth.yaml' -v `pwd`/filab_oauth.yaml:/tmp/filab_oauth.yaml --expose='8080' --link 'c9hub-api:c9hub-api' '10.0.5.241:5000/tai_ide/hub_common:v0' c9hub-dashboard
	core@cloud-ides ~ $ docker run -d --name 'backend-static-c9' -e 'C9TRACE=1' 'tai_c9/cloud9:v0' ./start_c9.sh
	core@cloud-ides ~ $ docker run --rm=true -t -i --name frontend-nginx -v '/var/run/docker.sock:/var/run/docker.sock'  --link 'c9hub-dashboard:c9hub-dashboard' --expose='443' --expose '8080' -p '0.0.0.0:443:443' -p '0.0.0.0:8080:8080' '10.0.5.241:5000/tai_ide/nginx:v0'


## Step 4: Browsing the application ##

The dashboard should be accessible via the `https` protocol on the `cloud-ides` host.
In the content of the preceding example, the url to browse is `https://130.206.85.162/`.

# Extra #

doorkeeper
[d](f)

ddd



[label]: url "title"
