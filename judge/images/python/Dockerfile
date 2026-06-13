FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    time \
    coreutils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 run \
    && mkdir -p /workspace \
    && chown -R run:run /workspace

WORKDIR /workspace
USER run

CMD ["sleep", "infinity"]
