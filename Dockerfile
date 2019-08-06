FROM python:3.7-buster

RUN mkdir -p /root/.config /config
RUN ln -s /config /root/.config/gphotos-sync 
VOLUME /config

RUN mkdir /storage
VOLUME /storage

RUN pip install gphotos-sync

ENTRYPOINT [ "gphotos-sync" ]