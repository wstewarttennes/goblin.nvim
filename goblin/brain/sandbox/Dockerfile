# Use an Alpine image for a lightweight container
FROM alpine:latest

# Install basic utilities and Docker
RUN apk add --no-cache bash docker-cli

# Create a directory for the incoming application
WORKDIR /sandbox

# Set an entrypoint that keeps the container running
ENTRYPOINT ["/bin/sh"]
