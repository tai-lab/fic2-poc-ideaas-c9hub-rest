all: build clean

archive_head:
	cd ../../.. && git archive --format=tar master | gzip -9 >etc/docker/c9hub-common/src.tar.gz

archive_stash:
	cd ../../.. && export C=`git stash create`; echo $$C; git archive --format tar $$C | gzip -9 >etc/docker/c9hub-common/src.tar.gz

build: archive_stash
	docker build --rm=true -t 'tai_ide/hub_common:v0' .

clean:
	git gc --prune=now

.PHONY: archive_head archive_stash build