ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    linux-headers \
    nginx \
    supervisor \
    curl \
    tzdata

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /share/eon-data /share/eon-output /var/log/supervisor /run/nginx

# Copy configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make run script executable
COPY run.sh /
RUN chmod a+x /run.sh

# Set permissions
RUN chown -R root:root /app && \
    chmod -R 755 /app

# Expose port
EXPOSE 8099

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8099/health || exit 1

# Labels
LABEL \
    io.hass.name="EON-SPOOKER" \
    io.hass.description="Process EON energy data files and import statistics to Home Assistant" \
    io.hass.arch="armhf|armv7|aarch64|amd64|i386" \
    io.hass.type="addon" \
    io.hass.version="3.0.0" \
    maintainer="EON-SPOOKER Contributors" \
    org.opencontainers.image.title="EON-SPOOKER" \
    org.opencontainers.image.description="Process EON energy data files and import statistics to Home Assistant" \
    org.opencontainers.image.vendor="EON-SPOOKER Contributors" \
    org.opencontainers.image.authors="EON-SPOOKER Contributors" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/Netesfiu/EON-SPOOKER" \
    org.opencontainers.image.source="https://github.com/Netesfiu/EON-SPOOKER" \
    org.opencontainers.image.documentation="https://github.com/Netesfiu/EON-SPOOKER" \
    org.opencontainers.image.created="2025-01-08T10:00:00Z" \
    org.opencontainers.image.revision="v3.0.0" \
    org.opencontainers.image.version="3.0.0"

# Run
CMD ["/run.sh"]
