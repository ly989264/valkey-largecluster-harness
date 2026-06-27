FROM python:3.11-slim

WORKDIR /opt/valkey-nodehost
COPY nodehost /opt/valkey-nodehost/nodehost
ENTRYPOINT ["/opt/valkey-nodehost/nodehost-entrypoint.sh"]
