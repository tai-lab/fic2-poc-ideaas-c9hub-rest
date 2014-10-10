FROM nginx:1.7.5

RUN apt-get update && \
    apt-get install -y wget
 
RUN wget --no-check-certificate -P /usr/local/bin https://godist.herokuapp.com/projects/ddollar/forego/releases/current/linux-amd64/forego && \
    chmod u+x /usr/local/bin/forego

RUN wget --no-check-certificate https://github.com/jwilder/docker-gen/releases/download/0.3.3/docker-gen-linux-amd64-0.3.3.tar.gz && \
    tar -C /usr/local/bin -xvzf docker-gen-linux-amd64-0.3.3.tar.gz && \
    rm docker-gen-linux-amd64-0.3.3.tar.gz

RUN mkdir /app /var/tmp/sites-enabled
WORKDIR /app
ADD app /app
ADD nginx /etc/nginx

EXPOSE 443

CMD ["forego", "start", "-r"]