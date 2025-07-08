ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3 \
    py3-pip \
    py3-pandas \
    py3-numpy \
    py3-yaml \
    py3-flask \
    py3-werkzeug \
    py3-requests \
    nginx \
    supervisor \
  && pip3 install --no-cache-dir \
    openpyxl \
    xlrd \
    python-dateutil \
    watchdog

# Copy data for add-on
COPY run.sh /
COPY eon_spooker/ /app/eon_spooker/
COPY EON_SPOOKER_v3.py /app/
COPY requirements.txt /app/
COPY addon/ /app/addon/
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create necessary directories
RUN mkdir -p /share/eon-data /share/eon-output /var/log/supervisor

# Set permissions
RUN chmod a+x /run.sh

# Set working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8099/health || exit 1

CMD [ "/run.sh" ]
