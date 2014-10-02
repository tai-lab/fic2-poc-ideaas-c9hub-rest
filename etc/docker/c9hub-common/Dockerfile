FROM python:3.4-onbuild

ADD src.tar.gz /usr/src/app/
CMD [ "python", "setup.py", "install" ]
CMD [ "which", "c9hub-api" ]