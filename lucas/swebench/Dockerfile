FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    git \
    patch \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy build script into container
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

# Script will be executed when container runs
ENTRYPOINT ["/app/run.sh"]
