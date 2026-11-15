FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        build-essential \
        python3 \
        python3-pip \
        usbutils \
        hackrf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY main.py /workspace/main.py
COPY src /workspace/src
COPY requirements.txt /workspace/requirements.txt

RUN pip3 install --no-cache-dir --break-system-packages -r /workspace/requirements.txt

ENTRYPOINT ["python3", "/workspace/main.py"]
CMD ["--mode", "software"]