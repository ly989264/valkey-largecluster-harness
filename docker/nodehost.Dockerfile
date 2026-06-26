FROM python:3.11-slim

ARG TARGETARCH

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/data/valkey-largecluster
ENV VALKEY_LARGECLUSTER_HOME=/data/valkey-largecluster
ENV VALKEY_SERVER=/usr/local/bin/valkey-server

WORKDIR /data/valkey-largecluster

COPY harness ./harness
COPY nodehost ./nodehost
COPY docker/nodehost-entrypoint.sh ./docker/nodehost-entrypoint.sh
COPY pyproject.toml README.md ./

RUN chmod +x ./docker/nodehost-entrypoint.sh \
    && mkdir -p /data/valkey-largecluster/runs

ENTRYPOINT ["./docker/nodehost-entrypoint.sh"]
CMD ["--help"]
