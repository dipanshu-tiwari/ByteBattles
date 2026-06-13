FROM alpine:latest

RUN apk add --no-cache \
    gcc \
    g++ \
    make \
    time \
    coreutils \
    ca-certificates \
    libc-dev

RUN adduser -D -u 1000 run && \
    mkdir -p /workspace && \
    chown -R run:run /workspace

WORKDIR /workspace
USER run

CMD ["sleep", "infinity"]
