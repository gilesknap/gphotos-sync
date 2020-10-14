FROM python:3-alpine AS gphotos-sync-builder

RUN apk add --update --no-cache gcc musl-dev linux-headers \
	&& rm -rf /var/cache/apk/*

ENV PYTHONDONTWRITEBYTECODE=1

RUN python -m venv --system-site-packages /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade gphotos-sync

FROM python:3-alpine

COPY --from=gphotos-sync-builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir -p /root/.config /config \
    && ln -s /config /root/.config/gphotos-sync \
    && mkdir /storage

VOLUME /config

VOLUME /storage

ENTRYPOINT [ "gphotos-sync" ]
